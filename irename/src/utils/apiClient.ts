import axios from 'axios';
import * as vscode from 'vscode';

// Create an Axios instance with default settings
const apiClient = axios.create();

// Add an interceptor to update the base URL dynamically
apiClient.interceptors.request.use(config => {
    const serverUrl = vscode.workspace.getConfiguration('renameit').get<string>('serverUrl');
    config.baseURL = serverUrl;
    return config;
});

export { apiClient };