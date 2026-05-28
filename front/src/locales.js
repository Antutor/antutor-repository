export const locales = {
  ko: {
    // Concepts
    inflation: '인플레이션',
    interestRate: '기준금리',
    exchangeRate: '환율',
    opportunityCost: '기회비용',
    compoundInterest: '복리',
    
    // Path Nodes
    fundamentals: '기본 개념',
    fundamentalsSummary: '선택한 주제의 핵심 원리입니다.',
    strategic: '전략적 분석',
    strategicSub: '적용 및 맥락',
    market: '시장 동향',
    risk: '리스크 관리',
    
    // Experts
    academicName: '학술 개념 전문가',
    academicRole: '기본 이론과 학문적 엄밀성에 중점을 둡니다.',
    marketName: '시장 실무 전문가',
    marketRole: '실제 시장 동향 및 데이터에 중점을 둡니다.',
    macroName: '거시 경제 전문가',
    macroRole: '글로벌 경제 지표 및 정책에 중점을 둡니다.',
    
    // Buttons & Header
    endSession: '학습 종료',
    logout: '로그아웃',
    
    // Main UI
    missionSelectTitle: '학습 미션을 선택하세요',
    missionSelectTitleUser: '님, 오늘의 학습 미션을 선택하세요!',
    antSleeping: '미션을 선택해주세요!',
    antReady: '학습할 준비가 되셨나요?',
    learningPath: '학습 경로',
    doingGreat: '정말 잘하고 있어요!',
    studyStreak: '연속 학습 {n}일째',
    attendance: '출석 현황',
    todayAttendance: '오늘({date}일) 출석 완료!',
    
    // Chat & System Messages
    preparingSession: '학습 세션을 준비하고 있습니다...',
    startFailed: '세션 시작에 실패했습니다. 다시 시도해주세요.',
    resumeFailed: '세션 재개 처리에 실패했습니다.',
    questionFailed: '첫 질문을 불러올 수 없습니다.',
    resumeSession: '이어서 학습하기',
    startFresh: '처음부터 다시하기',
    analyzingQuestion: '질문을 분석 중입니다...',
    connecting: '연결 중입니다...',
    hintIncludedL1: '1단계 힌트입니다. 방향만 살짝 제시해드립니다.',
    hintIncludedL2: '2단계 힌트입니다. 핵심 개념을 언급해드립니다.',
    hintIncludedL3: '3단계 힌트입니다. 빈칸 채우기를 진행합니다.',
    hintIncludedL4: '정답을 공개합니다.',
    fillBlankPlaceholder: '빈칸에 들어갈 내용을 입력하세요...',
    answerPlaceholder: '답변을 입력하세요...',
    fillBlankHelp: '아래 문장의 빈칸을 채워주세요.',
    nudgeHelp: '힌트를 참고하여 답변을 완성해 보세요.',
    cfProbeHelp: '카운터팩추얼 질문에 답해보세요.',
    iDontKnow: '모르겠어요',
    requestHint: '힌트 요청',
    
    // Sidebar
    myAiTeam: '나의 AI 전문가 팀',
    conceptDictTitle: '개념 사전',
    exploreAllConcepts: '모든 경제 용어 살펴보기',
    myProfile: '내 프로필',
    uploadProfilePic: '클릭하여 프로필 사진 업로드',
    
    // Expert Modal
    expertInsights: '전문가 통찰력',
    suggestedPerspective: '제안하는 관점',
    noFeedbackYet: '아직 이 전문가의 평가가 없습니다. 메시지를 보내보세요.',
    score: '스코어:',
    
    // Errors & Toasts
    connectionDelay: '연결 지연',
    delayMessage: '현재 접속자가 많아 AI 연결이 지연되고 있습니다.\n잠시 후 다시 시도해 주세요.',
    cancel: '취소',
    retry: '재시도',
    fallbackToast: '서버 혼잡으로 인해 임시 요약된 피드백을 제공합니다.',
    
    // Summary Modal
    accuracy: '정확성',
    practicality: '현실성',
    insight: '통찰력',
    noEvalData: '아직 평가 데이터가 없습니다.',
    sessionSummary: '학습 요약',
    achievementAnalysis: '학습 성취도 및 스타일 분석',
    knowledgeLevel: '지식 수준 지표',
    scaffoldingSummary: '학습 지원 요약',
    level1Hint: '1단계 힌트',
    level2Hint: '2단계 힌트',
    level3Hint: '3단계 힌트',
    selfDirectedBonus: '자기 주도 보너스',
    bonusEarned: '힌트 없이 세션을 완료하여\n{points}점의 보너스를 획득했습니다!',
    bonusMissed: '다음엔 힌트 없이\n세션을 완료하고\n기본 점수의 50%를\n보너스로 획득해보세요!',
    eduInsights: '학습 인사이트',
    evalResult: '평가 결과',
    
    // Dictionary
    searchPlaceholder: '개념 검색...',
    noResult: '검색 결과가 없습니다.',
    backToSession: '세션으로 돌아가기',
    searchTermsPlaceholder: '경제 용어 검색...',
    loadingDict: '사전 불러오는 중...',
    example: '예시:',
    returnWithHint: '힌트와 함께 채팅으로 돌아가기',
    
    // Review Modal
    conceptReview: '개념 복습: ',
    keySummary: '핵심 요약',
    defaultReviewSummary: '경제학의 기본 원칙은 수요와 공급에 대해 다루며, 인간의 동기에 따라 자원이 어떻게 동적으로 할당되는지를 설명합니다.',
    reviewInsight: '채팅으로 돌아가기 전에 이 메모를 주의 깊게 읽어보세요.',
    gotIt: '확인했어요!',

    // Resume Decision Buttons
    resumeSessionBtn: '이어서 학습하기',
    startFreshBtn: '처음부터 다시하기',

    // Chart Labels
    chartEmptyMsg: '학습을 진행하면\n점수 변화가 기록됩니다.',
    chartTurn: '턴',
    chartAccuracy: '정확성',
    chartPracticality: '현실성',
    chartInsight: '통찰력',
    radarNoData: '데이터가 없습니다.',
    
    // Dictionary Categories
    dictCatAcademic: '학술',
    dictCatMarket: '시장',
    dictCatMacro: '매크로',

    // Login Page
    loginWelcome: 'Antutor에 오신 것을 환영합니다',
    loginSubtitle: '학습 대시보드에 접속하려면 로그인하세요.',
    loginUserId: '아이디',
    loginUserIdPlaceholder: '아이디를 입력하세요',
    loginPassword: '비밀번호',
    loginPasswordPlaceholder: '비밀번호를 입력하세요',
    loginBtn: '로그인',
    loginFailed: '로그인 실패! 자격 증명을 확인하세요.',
    noAccount: '계정이 없으신가요?',
    signUp: '회원가입',

    // Resume last question label
    lastQuestion: '마지막 질문',

    // Register Page
    registerTitle: 'Antutor 가입하기',
    registerSubtitle: '계정을 만들고 학습을 시작하세요.',
    checkDuplicate: '중복 확인',
    registerBtn: '가입하기',
    alreadyHaveAccount: '이미 계정이 있으신가요?',
    goToLogin: '로그인',
    enterUserId: '아이디를 입력해주세요.',
    invalidUserId: '아이디는 영문 소문자와 숫자만 사용하여 최소 4자리 이상 입력해야 합니다.',
    usernameAvailable: '사용 가능한 아이디입니다!',
    usernameTaken: '이미 사용중인 아이디입니다.',
    serverConnectionError: '서버와 연결할 수 없습니다. 로컈 백엔드 서버가 실행 중인지 확인해주세요.',
    checkIdFirst: '아이디 중복 확인을 해주세요.',
    invalidPassword: '비밀번호는 영문 소문자와 숫자만 사용하여 최소 4자리 이상 입력해야 합니다.',
    registerSuccess: '가입 성공!',
    registerFailed: '회원가입에 실패했습니다.',
    inputRule: '아이디와 비밀번호는 영문 소문자와 숫자를 조합하여 최소 4자리 이상 입력해주세요.'
  },
  en: {
    // Concepts
    inflation: 'Inflation',
    interestRate: 'Interest Rate',
    exchangeRate: 'Exchange Rate',
    opportunityCost: 'Opportunity Cost',
    compoundInterest: 'Compound Interest',
    
    // Path Nodes
    fundamentals: 'Fundamentals',
    fundamentalsSummary: 'Core principles of the selected topic.',
    strategic: 'Strategic Analysis',
    strategicSub: 'Application & Context',
    market: 'Market Trends',
    risk: 'Risk Management',
    
    // Experts
    academicName: 'Academic Auditor',
    academicRole: 'Focuses on foundational theory and academic rigor.',
    marketName: 'Market Practitioner',
    marketRole: 'Focuses on real-world market trends and data.',
    macroName: 'Macro-Connector',
    macroRole: 'Focuses on global economic indicators and policies.',
    
    // Buttons & Header
    endSession: 'End Session',
    logout: 'Logout',
    
    // Main UI
    missionSelectTitle: 'Select a Learning Mission',
    missionSelectTitleUser: ', choose your learning mission for today!',
    antSleeping: 'Please select a mission!',
    antReady: 'Are you ready to learn?',
    learningPath: 'Learning Path',
    doingGreat: 'You are doing great!',
    studyStreak: '{n} Day Streak!',
    attendance: 'Attendance',
    todayAttendance: "Today's Check-in ({date})!",
    
    // Chat & System Messages
    preparingSession: 'Preparing learning session...',
    startFailed: 'Failed to start session. Please try again.',
    resumeFailed: 'Failed to resume session.',
    questionFailed: 'Failed to load the first question.',
    resumeSession: 'Resume Session',
    startFresh: 'Start Fresh',
    analyzingQuestion: 'Analyzing your question...',
    connecting: 'Connecting...',
    hintIncludedL1: 'Concept hint included.',
    hintIncludedL2: 'Concept example hint included.',
    hintIncludedL3: 'Fill-in-the-blank hint included.',
    hintIncludedL4: 'The answer is revealed.',
    fillBlankPlaceholder: 'Enter the missing word...',
    answerPlaceholder: 'Type your answer...',
    fillBlankHelp: 'Please fill in the blank in the sentence below.',
    nudgeHelp: 'Use the hint to complete your answer.',
    cfProbeHelp: 'Answer the counterfactual probe.',
    iDontKnow: "I don't know",
    requestHint: 'Request Hint',
    
    // Sidebar
    myAiTeam: 'My AI Expert Team',
    conceptDictTitle: 'Concept Dictionary',
    exploreAllConcepts: 'Explore all economic terms',
    myProfile: 'My Profile',
    uploadProfilePic: 'Click to upload a profile picture',
    
    // Expert Modal
    expertInsights: 'Expert Insights',
    suggestedPerspective: 'Suggested Perspective',
    noFeedbackYet: 'No feedback from this expert yet. Send a message.',
    score: 'Score:',
    
    // Errors & Toasts
    connectionDelay: 'Connection Delay',
    delayMessage: 'High traffic is causing AI connection delays.\nPlease try again in a moment.',
    cancel: 'Cancel',
    retry: 'Retry',
    fallbackToast: 'Due to server congestion, temporary summarized feedback is provided.',
    
    // Summary Modal
    accuracy: 'Accuracy',
    practicality: 'Practicality',
    insight: 'Insight',
    noEvalData: 'No evaluation data yet.',
    sessionSummary: 'Session Summary',
    achievementAnalysis: 'Learning achievement and style analysis',
    knowledgeLevel: 'Knowledge Level Indicators',
    scaffoldingSummary: 'Scaffolding Summary',
    level1Hint: 'Level 1 Hint',
    level2Hint: 'Level 2 Hint',
    level3Hint: 'Level 3 Hint',
    selfDirectedBonus: 'Self-Directed Bonus',
    bonusEarned: 'You earned {points} bonus points for completing without hints!',
    bonusMissed: 'Complete without hints next time to earn a 50% bonus on your base score!',
    eduInsights: 'Educational Insights',
    evalResult: 'Evaluation Result',
    
    // Dictionary
    searchPlaceholder: 'Search concepts...',
    noResult: 'No results found.',
    backToSession: 'Back to Session',
    searchTermsPlaceholder: 'Search economic terms...',
    loadingDict: 'Loading dictionary...',
    example: 'Example:',
    returnWithHint: 'Return to chat with hint',
    
    // Review Modal
    conceptReview: 'Concept Review: ',
    keySummary: 'Key Summary',
    defaultReviewSummary: 'The fundamental principles of economics cover supply and demand, explaining how resources are dynamically allocated based on human incentives.',
    reviewInsight: 'Please read this note carefully before returning to the chat.',
    gotIt: 'Got it!',

    // Resume Decision Buttons
    resumeSessionBtn: 'Resume Session',
    startFreshBtn: 'Start Fresh',

    // Chart Labels
    chartEmptyMsg: 'Complete a turn to\nsee score changes.',
    chartTurn: 'Turn',
    chartAccuracy: 'Accuracy',
    chartPracticality: 'Practicality',
    chartInsight: 'Insight',
    radarNoData: 'No data available.',

    // Dictionary Categories
    dictCatAcademic: 'Academic',
    dictCatMarket: 'Market',
    dictCatMacro: 'Macro',

    // Login Page
    loginWelcome: 'Welcome to Antutor',
    loginSubtitle: 'Sign in to access your learning dashboard.',
    loginUserId: 'Username',
    loginUserIdPlaceholder: 'Enter your username',
    loginPassword: 'Password',
    loginPasswordPlaceholder: 'Enter your password',
    loginBtn: 'Sign In',
    loginFailed: 'Login failed! Please check your credentials.',
    noAccount: "Don't have an account?",
    signUp: 'Sign Up',

    // Resume last question label
    lastQuestion: 'Last Question',

    // Register Page
    registerTitle: 'Join Antutor',
    registerSubtitle: 'Create an account and start learning.',
    checkDuplicate: 'Check',
    registerBtn: 'Sign Up',
    alreadyHaveAccount: 'Already have an account?',
    goToLogin: 'Sign In',
    enterUserId: 'Please enter a username.',
    invalidUserId: 'Username must be at least 4 lowercase letters and numbers.',
    usernameAvailable: 'Username is available!',
    usernameTaken: 'Username is already taken.',
    serverConnectionError: 'Cannot connect to server. Make sure the backend is running.',
    checkIdFirst: 'Please check username availability first.',
    invalidPassword: 'Password must be at least 4 lowercase letters and numbers.',
    registerSuccess: 'Registration successful!',
    registerFailed: 'Registration failed.',
    inputRule: 'ID and password must be at least 4 lowercase letters and numbers.'
  }
};

export const t = (lang, key) => {
    return locales[lang]?.[key] || locales['ko'][key] || key;
};
