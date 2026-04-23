import apiClient from './apiClient'

export const profileService = {
  /**
   * Get current user's profile with CV data
   */
  getProfile: async () => {
    try {
      const response = await apiClient.get('/profile')
      return response.data
    } catch (error) {
      console.error('Error fetching profile:', error)
      throw error
    }
  },

  /**
   * Update user's profile (CV data and/or telegram_id)
   * @param {Object} data - { cv_data?: {...}, telegram_id?: string }
   */
  updateProfile: async (data) => {
    try {
      const response = await apiClient.put('/profile', data)
      return response.data
    } catch (error) {
      console.error('Error updating profile:', error)
      throw error
    }
  },

  /**
   * Upload user avatar photo
   * @param {File} file - Image file
   */
  uploadAvatar: async (file) => {
    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await apiClient.post('/profile/avatar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      return response.data
    } catch (error) {
      console.error('Error uploading avatar:', error)
      throw error
    }
  }
}
