import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:3000', // 실제 서버 주소로 변경 가능
});

// 토큰이 필요한 요청에 자동으로 토큰을 실어 보내는 설정 (Interceptor)
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export default api;