import axios from 'axios';



const api = axios.create({
    // baseURL: 'https://elbert-expressible-deliciously.ngrok-free.dev', // 원격 서버 사용 시
    baseURL: 'http://localhost:8000', // 로컬 서버 사용 시
    timeout: 120000, // 120초 (AI 답변 생성 대기 시간 고려)
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