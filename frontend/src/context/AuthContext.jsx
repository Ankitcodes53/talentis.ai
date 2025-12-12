import { createContext, useContext, useState, useEffect } from 'react';
import api from '../api/axios';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    const token = localStorage.getItem('token');
    
    if (storedUser && token) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const response = await api.post('/api/login', { email, password });
    const { access_token, user_role, user_id } = response.data;
    
    localStorage.setItem('token', access_token);
    const userData = { id: user_id, email, role: user_role };
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
    
    return userData;
  };

  const register = async (email, password, role, company_name, full_name) => {
    const response = await api.post('/api/register', {
      email,
      password,
      role,
      company_name,
      full_name,
    });
    const { access_token, user_role, user_id } = response.data;
    
    localStorage.setItem('token', access_token);
    const userData = { id: user_id, email, role: user_role };
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
    
    return userData;
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
