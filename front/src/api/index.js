import axios from 'axios';



const api = axios.create({
    baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8080',
    timeout: 600000, // 600초 (고성능 모델 토론 대기 위해 10분으로 연장)
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