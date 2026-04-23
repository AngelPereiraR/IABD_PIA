import useStore from '../../stores/globalStore';

export function useAuth() {
  const { user, token, isLoading, error } = useStore((state) => state.auth);
  const authActions = useStore((state) => state.authActions);

  return {
    user,
    token,
    isLoading,
    error,
    login: authActions.login,
    registerUser: authActions.registerUser,
    googleCallback: authActions.googleCallback,
    logout: authActions.logout,
    isAuthenticated: !!token,
  };
}
