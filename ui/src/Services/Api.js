// =============================================================
// Api.js — same for both Basic RAG and LlamaIndex
// =============================================================

import axios from "axios";

const axiosInstance = axios.create({
    baseURL: "http://localhost:8080",
    headers: {
        "Content-Type": "application/json"
    }
});

// upload zip → get session_id back
export const uploadZip = async (zipFile) => {
    const formData = new FormData();
    formData.append("file", zipFile);

    const response = await axiosInstance.post("/api/upload", formData, {
        headers: {
            "Content-Type": "multipart/form-data"
        }
    });

    return response.data.session_id;
}

export default axiosInstance;
