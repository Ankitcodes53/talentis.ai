import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import api from '../api/axios';
import AnimatedBackground from '../components/AnimatedBackground';

const Home = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreatePost, setShowCreatePost] = useState(false);
  const [newPost, setNewPost] = useState({
    content: '',
    post_type: 'general'
  });

  useEffect(() => {
    fetchPosts();
  }, []);

  const fetchPosts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/posts');
      setPosts(response.data.posts || []);
    } catch (error) {
      console.error('Error fetching posts:', error);
      toast.error('Failed to load posts');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePost = async (e) => {
    e.preventDefault();
    if (!newPost.content.trim()) {
      toast.error('Post content cannot be empty');
      return;
    }

    try {
      const response = await api.post('/api/posts', newPost);
      setPosts([response.data, ...posts]);
      setNewPost({ content: '', post_type: 'general' });
      setShowCreatePost(false);
      toast.success('Post created successfully!');
    } catch (error) {
      console.error('Error creating post:', error);
      toast.error('Failed to create post');
    }
  };

  const handleLike = async (postId) => {
    try {
      const response = await api.post(`/api/posts/${postId}/like`);
      setPosts(posts.map(post => {
        if (post.id === postId) {
          return {
            ...post,
            is_liked: response.data.liked,
            likes_count: response.data.liked ? post.likes_count + 1 : post.likes_count - 1
          };
        }
        return post;
      }));
    } catch (error) {
      console.error('Error toggling like:', error);
      toast.error('Failed to update like');
    }
  };

  const handleDeletePost = async (postId) => {
    if (!window.confirm('Are you sure you want to delete this post?')) return;

    try {
      await api.delete(`/api/posts/${postId}`);
      setPosts(posts.filter(post => post.id !== postId));
      toast.success('Post deleted successfully');
    } catch (error) {
      console.error('Error deleting post:', error);
      toast.error('Failed to delete post');
    }
  };

  const getTimeDiff = (dateString) => {
    const now = new Date();
    const postDate = new Date(dateString);
    const diffMs = now - postDate;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return postDate.toLocaleDateString();
  };

  const getPostTypeColor = (type) => {
    switch(type) {
      case 'job_opening': return 'bg-blue-100 text-blue-800';
      case 'achievement': return 'bg-green-100 text-green-800';
      case 'question': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPostTypeLabel = (type) => {
    switch(type) {
      case 'job_opening': return '💼 Job Opening';
      case 'achievement': return '🎉 Achievement';
      case 'question': return '❓ Question';
      default: return '📝 Post';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-teal-50">
      <AnimatedBackground />
      
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-lg border-b border-purple-100 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <motion.h1
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-teal-500 bg-clip-text text-transparent cursor-pointer"
              onClick={() => navigate('/')}
            >
              Talentis.AI
            </motion.h1>

            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/explore')}
                className="px-4 py-2 text-purple-600 hover:bg-purple-50 rounded-lg transition-all font-medium"
              >
                🔍 Explore Jobs
              </button>
              <button
                onClick={() => navigate(user?.role === 'employer' ? '/employer' : '/candidate')}
                className="px-4 py-2 text-purple-600 hover:bg-purple-50 rounded-lg transition-all font-medium"
              >
                📊 Dashboard
              </button>
              <button
                onClick={logout}
                className="px-4 py-2 bg-gradient-to-r from-purple-600 to-teal-500 text-white rounded-lg hover:shadow-lg transition-all font-semibold"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Welcome Banner */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-purple-600 to-teal-500 rounded-2xl p-8 mb-6 text-white shadow-xl"
        >
          <h2 className="text-3xl font-bold mb-2">
            Welcome back, {user?.email?.split('@')[0] || 'User'}! 👋
          </h2>
          <p className="text-purple-100">
            {user?.role === 'employer' 
              ? 'Share job openings, company updates, and connect with top talent.'
              : 'Share your achievements, ask questions, and connect with employers.'}
          </p>
        </motion.div>

        {/* Create Post Button */}
        <motion.button
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setShowCreatePost(true)}
          className="fixed bottom-8 right-8 w-16 h-16 bg-gradient-to-r from-purple-600 to-teal-500 text-white rounded-full shadow-2xl hover:shadow-purple-500/50 transition-all flex items-center justify-center text-3xl z-50"
        >
          +
        </motion.button>

        {/* Create Post Modal */}
        <AnimatePresence>
          {showCreatePost && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
              onClick={() => setShowCreatePost(false)}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                onClick={(e) => e.stopPropagation()}
                className="bg-white rounded-2xl p-6 max-w-2xl w-full shadow-2xl"
              >
                <h3 className="text-2xl font-bold text-gray-800 mb-4">Create a Post</h3>
                <form onSubmit={handleCreatePost}>
                  <select
                    value={newPost.post_type}
                    onChange={(e) => setNewPost({ ...newPost, post_type: e.target.value })}
                    className="w-full px-4 py-2 rounded-lg border-2 border-gray-200 focus:border-purple-500 outline-none mb-4"
                  >
                    <option value="general">General Post</option>
                    <option value="job_opening">Job Opening</option>
                    <option value="achievement">Achievement</option>
                    <option value="question">Question</option>
                  </select>

                  <textarea
                    value={newPost.content}
                    onChange={(e) => setNewPost({ ...newPost, content: e.target.value })}
                    placeholder="What's on your mind?"
                    className="w-full px-4 py-3 rounded-lg border-2 border-gray-200 focus:border-purple-500 outline-none resize-none h-32 mb-4"
                    required
                  />

                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={() => setShowCreatePost(false)}
                      className="flex-1 px-6 py-3 border-2 border-gray-200 rounded-lg font-semibold hover:bg-gray-50 transition-all"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-600 to-teal-500 text-white rounded-lg font-semibold hover:shadow-lg transition-all"
                    >
                      Post
                    </button>
                  </div>
                </form>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Posts Feed */}
        <div className="space-y-4">
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-4 border-purple-600 border-t-transparent mx-auto"></div>
              <p className="text-gray-500 mt-4">Loading posts...</p>
            </div>
          ) : posts.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-12 bg-white/80 backdrop-blur-lg rounded-2xl border border-purple-100"
            >
              <p className="text-2xl mb-2">📭</p>
              <p className="text-gray-600 font-medium">No posts yet</p>
              <p className="text-gray-500 text-sm mt-2">Be the first to share something!</p>
            </motion.div>
          ) : (
            posts.map((post, index) => (
              <motion.div
                key={post.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="bg-white/80 backdrop-blur-lg rounded-2xl border border-purple-100 shadow-lg overflow-hidden hover:shadow-xl transition-all"
              >
                <div className="p-6">
                  {/* Post Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-start gap-3">
                      <div className="w-12 h-12 rounded-full bg-gradient-to-r from-purple-600 to-teal-500 flex items-center justify-center text-white font-bold text-lg">
                        {post.author_name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <h4 className="font-bold text-gray-800">{post.author_name}</h4>
                        {post.company_name && (
                          <p className="text-sm text-gray-600">{post.company_name}</p>
                        )}
                        <p className="text-xs text-gray-500">
                          {post.author_role === 'employer' ? '👔 Employer' : '👤 Candidate'} · {getTimeDiff(post.created_at)}
                        </p>
                      </div>
                    </div>
                    {post.user_id === user?.id && (
                      <button
                        onClick={() => handleDeletePost(post.id)}
                        className="text-red-500 hover:bg-red-50 p-2 rounded-lg transition-all"
                      >
                        🗑️
                      </button>
                    )}
                  </div>

                  {/* Post Type Badge */}
                  <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold mb-3 ${getPostTypeColor(post.post_type)}`}>
                    {getPostTypeLabel(post.post_type)}
                  </span>

                  {/* Post Content */}
                  <p className="text-gray-700 whitespace-pre-wrap mb-4">{post.content}</p>

                  {/* Post Media */}
                  {post.media_url && (
                    <img
                      src={post.media_url}
                      alt="Post media"
                      className="w-full rounded-lg mb-4"
                    />
                  )}

                  {/* Post Actions */}
                  <div className="flex items-center gap-6 pt-4 border-t border-gray-100">
                    <button
                      onClick={() => handleLike(post.id)}
                      className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                        post.is_liked 
                          ? 'bg-red-50 text-red-600' 
                          : 'hover:bg-gray-50 text-gray-600'
                      }`}
                    >
                      {post.is_liked ? '❤️' : '🤍'} {post.likes_count}
                    </button>
                  </div>
                </div>
              </motion.div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default Home;
