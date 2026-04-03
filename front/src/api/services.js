import api from './index';

export const authAPI = {
    register: (data) => api.post('/register', data), // 1번
    login: (formData) => api.post('/token', formData, { // 2번: Form-Data 형식
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }),
};

export const dictionaryAPI = {
    getList: () => api.get('/dictionary'), // 3번
    getDetail: (term) => api.get(`/dictionary/${term}`), // 4번
};

export const studyAPI = {
    startSession: (concept) => api.get(`/start/${concept}`), // 5번
    sendChat: (data) => api.post('/chat', data), // 6번 (스캐폴딩 로직 포함)
    getReport: (sessionId) => api.get(`/report/${sessionId}`), // 7번 (레이더 차트용)
    getMyStats: () => api.get('/stats/me'), // 8번
};