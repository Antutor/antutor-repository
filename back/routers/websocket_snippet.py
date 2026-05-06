@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # 1. 초기 인증 및 데이터 수신
        data = await websocket.receive_json()
        token = data.get("token")
        session_id = data.get("session_id")
        user_answer = data.get("user_answer")
        
        if not token or not session_id or not user_answer:
            await websocket.send_json({"type": "error", "message": "Missing required fields (token, session_id, user_answer)."})
            await websocket.close(code=1008)
            return
            
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if not username:
                raise ValueError("Invalid token")
        except Exception as e:
            await websocket.send_json({"type": "error", "message": "Authentication failed."})
            await websocket.close(code=1008)
            return
            
        user_res = supabase.table("users").select("*").eq("username", username).execute()
        if not user_res.data:
            await websocket.send_json({"type": "error", "message": "User not found."})
            await websocket.close(code=1008)
            return
            
        current_user = user_res.data[0]
        user_id = current_user["user_id"]
        
        # 2. 세션 및 개념 데이터 조회
        await websocket.send_json({"type": "status", "message": "🔍 Checking session data..."})
        
        sess_res = supabase.table("sessions").select("*").eq("session_id", int(session_id)).execute()
        if not sess_res.data:
            await websocket.send_json({"type": "error", "message": "Invalid Session ID."})
            await websocket.close()
            return
        session = sess_res.data[0]
        
        if session["user_id"] != user_id:
            await websocket.send_json({"type": "error", "message": "Not authorized to access this session."})
            await websocket.close()
            return
            
        db_concept_id = session["concept_id"]
        concept_res = supabase.table("concepts").select("*").eq("concept_id", db_concept_id).execute()
        if not concept_res.data:
            await websocket.send_json({"type": "error", "message": "Target Concept is not supported."})
            await websocket.close()
            return
            
        concept_data = concept_res.data[0]
        concept_name = concept_data["name"]
        ground_truth = concept_data["definition"]
        
        eval_user_answer = await translate_ko_to_en(user_answer)
        is_give_up = any(kw in user_answer.lower() or kw in eval_user_answer.lower() for kw in GIVE_UP_KEYWORDS)
        
        await websocket.send_json({"type": "status", "message": "🌐 Searching Knowledge Graph & News..."})
        
        concept_name_kr = await translate_en_to_ko(concept_name)
        news_context, kg_context = await asyncio.gather(
            retrieve_news_rag(concept_name),
            retrieve_knowledge_graph(concept_name_kr)
        )
        
        initial_state = {
            "concept": concept_name,
            "user_answer": eval_user_answer,
            "ground_truth": ground_truth,
            "news_context": news_context,
            "kg_context": kg_context,
            "draft_reviews": {},
            "critiques": [],
            "raw_scores": {},
            "is_contradiction": False,
            "final_synthesis": "",
            "debate_count": 0,
            "moderator_action": "",
            "consecutive_high_score_count": session.get("consecutive_high_score_count", 0),
            "hint_provided": False
        }
        
        await websocket.send_json({"type": "status", "message": "🤖 AI Agents are drafting & debating..."})
        
        final_state = None
        
        if is_give_up:
            final_state = initial_state
            final_state["raw_scores"] = {"The Market Practitioner": 0.0, "The Macro-Connector": 0.0, "The Academic Auditor": 0.0}
            final_state["is_contradiction"] = False
            final_state["final_synthesis"] = "You requested help."
        else:
            async for event in debate_graph.astream_events(initial_state, version="v1"):
                kind = event["event"]
                
                if kind == "on_chat_model_stream":
                    tags = event.get("tags", [])
                    if "synthesis_llm" in tags:
                        chunk = event["data"]["chunk"]
                        if chunk.content:
                            await websocket.send_json({"type": "stream", "chunk": chunk.content})
                
                elif kind == "on_chain_end":
                    if event["name"] == "LangGraph":
                        final_state = event["data"]["output"]
        
        await websocket.send_json({"type": "status", "message": "✅ Finalizing response..."})
        
        expert_scores_raw = final_state.get("raw_scores", {})
        antutor_score = expert_scores_raw.get("The Academic Auditor", 0.0)
        is_contradiction = final_state.get("is_contradiction", False)
        hint_provided = final_state.get("hint_provided", False)
        
        if hint_provided:
            current_scaffold_count = session.get("scaffolding_counter", 0)
            supabase.table("sessions").update({"scaffolding_counter": current_scaffold_count + 1}).eq("session_id", session["session_id"]).execute()
            
        expert_results = []
        any_fallback = False
        for persona, review in final_state.get("draft_reviews", {}).items():
            fallback_flag = review.get("is_fallback", False) if isinstance(review, dict) else False
            if fallback_flag:
                any_fallback = True
            expert_results.append({
                "persona": persona,
                "score": expert_scores_raw.get(persona, 0.75),
                "feedback": review,
                "is_fallback": fallback_flag
            })
            
        expert_scores = expert_scores_raw
        
        save_debate_log(
            session_id=session["session_id"],
            concept=concept_name,
            user_answer=eval_user_answer,
            draft_reviews=final_state.get("draft_reviews", {}),
            critiques=final_state.get("critiques", []),
            final_synthesis=final_state.get("final_synthesis", "")
        )
        
        if is_contradiction:
            antutor_score = 0.0
            propositions = ["Local LLM Blocked: Explicit contradiction found."]
            expert_results = [{"persona": "System", "score": 0.0, "feedback": "Answer contradicts the ground truth."}]
            expert_scores = {"System": 0.0, "The Market Practitioner": 0.0, "The Macro-Connector": 0.0, "The Academic Auditor": 0.0}
            lowest_persona = "System"
        elif is_give_up:
            propositions = []
            lowest_persona = "System"
        else:
            propositions = ["(Evaluated by Multi-Agent Debate Graph)"]
            lowest_persona = min(expert_scores.keys(), key=lambda k: expert_scores[k]) if expert_scores else "System"
            
        raw_avg_score = (
            expert_scores.get("The Academic Auditor", 0) * 100 +
            expert_scores.get("The Market Practitioner", 0) * 100 +
            expert_scores.get("The Macro-Connector", 0) * 100
        ) / 3.0 if expert_scores else 0.0

        moderator_action = "proceed"
        scaffold_plan = None
        current_idk_count = session["idk_count"]
        guidance_message = ""
        
        if is_give_up:
            current_idk_count += 1
            supabase.table("sessions").update({"idk_count": current_idk_count}).eq("session_id", session["session_id"]).execute()
            moderator_action = "scaffold"
            backtrack_id = concept_data.get("backtrack_id")
            backtrack_res = supabase.table("concepts").select("*").eq("name", backtrack_id).execute()
            if not backtrack_res.data:
                backtrack_res = supabase.table("concepts").select("*").eq("concept_id", backtrack_id).execute()
            backtrack_name = backtrack_res.data[0]["name"] if backtrack_res.data else backtrack_id
            
            if current_idk_count == 1:
                backtrack_question = f"Before we proceed, can you explain what {backtrack_name} is?"
                guidance_message = backtrack_question
                scaffold_plan = {"step": "Sub-concept Nudge", "message": backtrack_question}
            else:
                dict_content = backtrack_res.data[0].get("dict_content", "") if backtrack_res.data else ""
                guidance_message = "It looks like you need help. Here is the concept dictionary link."
                scaffold_plan = {"step": "Concept Dictionary Link", "message": guidance_message, "dictionary_link": f"/dictionary/{backtrack_name}", "definition": dict_content}
        else:
            if raw_avg_score >= 85:
                moderator_action = "suggest_termination"
                guidance_message = "You have achieved a high level of mastery. Would you like to terminate the session? (Yes/No)"
                scaffold_plan = {"step": "Termination Suggestion", "message": guidance_message}
            elif is_contradiction:
                moderator_action = "retry"
                guidance_message = "Your answer seems to contradict the core facts. Please review the concept once more or ask for a 'hint'!"
                scaffold_plan = {"step": "Retry Prompt", "message": guidance_message}
            else:
                moderator_action = "proceed"
                guidance_message = final_state.get("final_synthesis", "Good job, but let's explore more deeply.")
                scaffold_plan = {"step": "Guidance Prompt", "message": guidance_message}

        logs_count_res = supabase.table("chat_logs").select("log_id", count="exact").eq("session_id", session["session_id"]).execute()
        turn_number = logs_count_res.count + 1 if logs_count_res.count is not None else 1

        chat_log_payload = {
            "session_id": session["session_id"],
            "turn_number": turn_number,
            "user_message": user_answer,
            "score_academic": antutor_score,
            "score_market": expert_scores.get("The Market Practitioner", 0),
            "score_macro": expert_scores.get("The Macro-Connector", 0),
            "selected_agent": lowest_persona,
            "ai_response": guidance_message
        }
        
        supabase.table("chat_logs").insert(chat_log_payload).execute()
        
        translated_propositions = [await translate_en_to_ko(p) for p in propositions]
        for expert in expert_results:
            raw_feedback = expert.get("feedback")
            if isinstance(raw_feedback, dict):
                actual_text = raw_feedback.get("feedback", "")
                expert["feedback"] = await translate_en_to_ko(actual_text) if actual_text else ""
            elif isinstance(raw_feedback, str):
                expert["feedback"] = await translate_en_to_ko(raw_feedback)
                
        if scaffold_plan:
            if scaffold_plan.get("message"):
                scaffold_plan["message"] = await translate_en_to_ko(scaffold_plan["message"])
            if scaffold_plan.get("definition"):
                scaffold_plan["definition"] = await translate_en_to_ko(scaffold_plan["definition"])

        await websocket.send_json({
            "type": "final_result",
            "data": {
                "atomic_propositions": translated_propositions,
                "expert_average_score": raw_avg_score,
                "is_contradiction_override": is_contradiction,
                "expert_feedback": expert_results,
                "is_fallback": any_fallback,
                "moderator_decision": {
                    "status": moderator_action,
                    "lowest_performing_area": lowest_persona,
                    "scaffold_plan": scaffold_plan
                }
            }
        })
        
        await asyncio.sleep(1)
        await websocket.close()
        
    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket Error: {e}")
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json({"type": "error", "message": str(e)})
                await websocket.close(code=1011)
        except Exception:
            pass
