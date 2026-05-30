const BASE_URL = import.meta.env.MODE === 'development' ? '' : (import.meta.env.VITE_API_URL || 'https://neatnode.onrender.com');
export default BASE_URL;
