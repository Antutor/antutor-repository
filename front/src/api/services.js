import api from './index';



export const authAPI = {
    checkUsername: (username) => api.get('/check-username', { params: { username } }), // 1.1 아이디 중복 확인
    register: (data) => api.post('/register', data), // 1.2 회원가입
    login: (data) => {
        const params = new URLSearchParams();
        params.append('username', data.username);
        params.append('password', data.password);
        return api.post('/token', params, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
    }, // 1.3 로그인 및 토큰 발급
};

export const dictionaryAPI = {
    getList: (language = 'ko') => api.get('/dictionary', { params: { language } }), // 2.1 전체 개념 목록 조회
    getDetail: (term, language = 'ko') => api.get(`/dictionary/${term}`, { params: { language } }), // 2.2 단일 개념 상세 조회
};

export const studyAPI = {
    startSession: (concept, language = 'ko') => api.get(`/start/${concept}`, { params: { language } }), // 3.1 학습 세션 시작
    resolveResume: (data) => api.post('/resolve_resume', data), // 3.1.5 세션 재개 결정
    sendChat: (data) => api.post('/chat', data), // 3.2 챗봇 답변 제출 및 평가
    endSession: (data) => api.post('/end_session', data), // 3.3 학습 세션 종료 및 통계 반환
};

export const sandboxAPI = {
    testPrompt: (data) => api.post('/ai/test/sandbox', data), // 4.1 프롬프트 튜닝 샌드박스
};

export const quizAPI = {
    getQuestions: (concept) => api.get(`/quiz/${concept}`), // 5.1 개념별 퀴즈 조회
    submitQuiz: (data) => api.post('/quiz/submit', data), // 5.2 퀴즈 결과 제출
};