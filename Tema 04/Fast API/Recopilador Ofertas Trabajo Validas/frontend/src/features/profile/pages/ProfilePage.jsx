import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, Plus, Trash2, Save, AlertCircle, CheckCircle } from 'lucide-react'
import { profileService } from '../../../services/profileService'
import { Layout, Spinner } from '../../../shared/components'

export default function ProfilePage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState({ type: '', text: '' })
  const [isAdmin, setIsAdmin] = useState(false)

  const [profile, setProfile] = useState({
    email: '',
    telegram_id: null,
    avatar_url: null,
    cv_data: {
      nombre: '',
      email: '',
      linkedin: '',
      github: '',
      telefono: '',
      ubicacion: '',
      web: '',
      resumen_base: '',
      formacion: [],
      experiencia_base: [],
      proyectos: [],
      habilidades_base: {},
      idiomas: [],
      certificaciones: [],
      cursos: [],
      voluntariado: []
    }
  })

  const [preview, setPreview] = useState(null)
  const [newSkillCategory, setNewSkillCategory] = useState('')
  const [newSkillName, setNewSkillName] = useState('')
  const [expandedSections, setExpandedSections] = useState({
    datosPersonales: true,
    resumen: true,
    habilidades: false,
    formacion: false,
    experiencia: false,
    proyectos: false,
    idiomas: false,
    certificaciones: false,
    cursos: false,
    voluntariado: false
  })

  // Cargar perfil al montar
  useEffect(() => {
    loadProfile()
  }, [])

  const loadProfile = async () => {
    try {
      setLoading(true)
      const data = await profileService.getProfile()
      setProfile(data)
      setIsAdmin(data.telegram_id !== null && data.telegram_id !== undefined)
      setMessage({ type: '', text: '' })
    } catch (error) {
      setMessage({
        type: 'error',
        text: 'Error loading profile: ' + (error.response?.data?.detail || error.message)
      })
    } finally {
      setLoading(false)
    }
  }

  const handleAvatarChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = () => setPreview(reader.result)
      reader.readAsDataURL(file)
      uploadAvatar(file)
    }
  }

  const uploadAvatar = async (file) => {
    try {
      const result = await profileService.uploadAvatar(file)
      setProfile(prev => ({ ...prev, avatar_url: result.avatar_url }))
      setMessage({ type: 'success', text: 'Profile picture updated' })
      setTimeout(() => setMessage({ type: '', text: '' }), 3000)
    } catch (error) {
      setMessage({
        type: 'error',
        text: 'Error uploading photo: ' + (error.response?.data?.detail || error.message)
      })
    }
  }

  const updateCVData = (field, value) => {
    setProfile(prev => ({
      ...prev,
      cv_data: { ...prev.cv_data, [field]: value }
    }))
  }

  const addFormacion = () => {
    setProfile(prev => ({
      ...prev,
      cv_data: {
        ...prev.cv_data,
        formacion: [...prev.cv_data.formacion, { titulo: '', centro: '', anio: '' }]
      }
    }))
  }

  const updateFormacion = (index, field, value) => {
    setProfile(prev => ({
      ...prev,
      cv_data: {
        ...prev.cv_data,
        formacion: prev.cv_data.formacion.map((item, i) =>
          i === index ? { ...item, [field]: value } : item
        )
      }
    }))
  }

  const removeFormacion = (index) => {
    setProfile(prev => ({
      ...prev,
      cv_data: {
        ...prev.cv_data,
        formacion: prev.cv_data.formacion.filter((_, i) => i !== index)
      }
    }))
  }

  const addExperiencia = () => {
    setProfile(prev => ({
      ...prev,
      cv_data: {
        ...prev.cv_data,
        experiencia_base: [...prev.cv_data.experiencia_base, { puesto: '', empresa: '', duracion: '', logros: [] }]
      }
    }))
  }

  const updateExperiencia = (index, field, value) => {
    setProfile(prev => ({
      ...prev,
      cv_data: {
        ...prev.cv_data,
        experiencia_base: prev.cv_data.experiencia_base.map((item, i) =>
          i === index ? { ...item, [field]: value } : item
        )
      }
    }))
  }

  const removeExperiencia = (index) => {
    setProfile(prev => ({
      ...prev,
      cv_data: {
        ...prev.cv_data,
        experiencia_base: prev.cv_data.experiencia_base.filter((_, i) => i !== index)
      }
    }))
  }

  const addProyecto = () => {
    setProfile(prev => ({
      ...prev,
      cv_data: {
        ...prev.cv_data,
        proyectos: [...prev.cv_data.proyectos, { nombre: '', descripcion: '', tecnologias: [] }]
      }
    }))
  }

  const updateProyecto = (index, field, value) => {
    setProfile(prev => ({
      ...prev,
      cv_data: {
        ...prev.cv_data,
        proyectos: prev.cv_data.proyectos.map((item, i) =>
          i === index ? { ...item, [field]: value } : item
        )
      }
    }))
  }

  const removeProyecto = (index) => {
    setProfile(prev => ({
      ...prev,
      cv_data: {
        ...prev.cv_data,
        proyectos: prev.cv_data.proyectos.filter((_, i) => i !== index)
      }
    }))
  }

  const addIdioma = () => {
    setProfile(prev => ({
      ...prev,
      cv_data: {
        ...prev.cv_data,
        idiomas: [...prev.cv_data.idiomas, { idioma: '', nivel: '' }]
      }
    }))
  }

  const updateIdioma = (index, field, value) => {
    setProfile(prev => ({
      ...prev,
      cv_data: {
        ...prev.cv_data,
        idiomas: prev.cv_data.idiomas.map((item, i) =>
          i === index ? { ...item, [field]: value } : item
        )
      }
    }))
  }

  const removeIdioma = (index) => {
    setProfile(prev => ({
      ...prev,
      cv_data: {
        ...prev.cv_data,
        idiomas: prev.cv_data.idiomas.filter((_, i) => i !== index)
      }
    }))
  }

  const addCertificacion = () => {
    setProfile(prev => ({
      ...prev,
      cv_data: {
        ...prev.cv_data,
        certificaciones: [...prev.cv_data.certificaciones, { nombre: '', emisor: '', anio: '' }]
      }
    }))
  }

  const updateCertificacion = (index, field, value) => {
    setProfile(prev => ({
      ...prev,
      cv_data: {
        ...prev.cv_data,
        certificaciones: prev.cv_data.certificaciones.map((item, i) =>
          i === index ? { ...item, [field]: value } : item
        )
      }
    }))
  }

  const removeCertificacion = (index) => {
    setProfile(prev => ({
      ...prev,
      cv_data: {
        ...prev.cv_data,
        certificaciones: prev.cv_data.certificaciones.filter((_, i) => i !== index)
      }
    }))
  }

  const addCurso = () => {
    setProfile(prev => ({
      ...prev,
      cv_data: {
        ...prev.cv_data,
        cursos: [...prev.cv_data.cursos, { nombre: '', plataforma: '', anio: '' }]
      }
    }))
  }

  const updateCurso = (index, field, value) => {
    setProfile(prev => ({
      ...prev,
      cv_data: {
        ...prev.cv_data,
        cursos: prev.cv_data.cursos.map((item, i) =>
          i === index ? { ...item, [field]: value } : item
        )
      }
    }))
  }

  const removeCurso = (index) => {
    setProfile(prev => ({
      ...prev,
      cv_data: {
        ...prev.cv_data,
        cursos: prev.cv_data.cursos.filter((_, i) => i !== index)
      }
    }))
  }

  const addVoluntariado = () => {
    setProfile(prev => ({
      ...prev,
      cv_data: {
        ...prev.cv_data,
        voluntariado: [...prev.cv_data.voluntariado, { organizacion: '', rol: '', descripcion: '', anio: '' }]
      }
    }))
  }

  const updateVoluntariado = (index, field, value) => {
    setProfile(prev => ({
      ...prev,
      cv_data: {
        ...prev.cv_data,
        voluntariado: prev.cv_data.voluntariado.map((item, i) =>
          i === index ? { ...item, [field]: value } : item
        )
      }
    }))
  }

  const removeVoluntariado = (index) => {
    setProfile(prev => ({
      ...prev,
      cv_data: {
        ...prev.cv_data,
        voluntariado: prev.cv_data.voluntariado.filter((_, i) => i !== index)
      }
    }))
  }

  const addHabilidad = (categoria, skill) => {
    setProfile(prev => ({
      ...prev,
      cv_data: {
        ...prev.cv_data,
        habilidades_base: {
          ...prev.cv_data.habilidades_base,
          [categoria]: [...(prev.cv_data.habilidades_base[categoria] || []), skill]
        }
      }
    }))
  }

  const removeHabilidad = (categoria, index) => {
    setProfile(prev => {
      const updatedSkills = prev.cv_data.habilidades_base[categoria].filter((_, i) => i !== index)
      const newHabilidades = { ...prev.cv_data.habilidades_base }

      if (updatedSkills.length === 0) {
        delete newHabilidades[categoria]
      } else {
        newHabilidades[categoria] = updatedSkills
      }

      return {
        ...prev,
        cv_data: {
          ...prev.cv_data,
          habilidades_base: newHabilidades
        }
      }
    })
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      const updateData = { cv_data: profile.cv_data }

      // Only add telegram_id if admin and changed
      if (isAdmin && profile.telegram_id) {
        updateData.telegram_id = profile.telegram_id
      }

      await profileService.updateProfile(updateData)
      setMessage({ type: 'success', text: 'Profile saved successfully' })
      setTimeout(() => setMessage({ type: '', text: '' }), 3000)
    } catch (error) {
      const detail = error.response?.data?.detail
      if (detail && detail.includes('admin')) {
        setMessage({ type: 'error', text: 'You do not have permission to update telegram_id' })
      } else {
        setMessage({ type: 'error', text: 'Error saving profile: ' + (detail || error.message) })
      }
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <Layout>
        <Spinner message="Loading profile..." fullHeight />
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-8 mb-8">
          <div className="flex items-start gap-8">
            {/* Avatar */}
            <div className="relative">
              <div className="w-32 h-32 rounded-full bg-gray-200 flex items-center justify-center overflow-hidden">
                {preview || profile.avatar_url ? (
                  <img
                    src={preview || profile.avatar_url}
                    alt="Avatar"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="text-gray-400 text-4xl">👤</div>
                )}
              </div>
              <label className="absolute bottom-0 right-0 bg-blue-600 text-white p-2 rounded-full cursor-pointer hover:bg-blue-700">
                <Upload size={20} />
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleAvatarChange}
                  className="hidden"
                />
              </label>
            </div>

            {/* Info */}
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {profile.cv_data.nombre || 'No name'}
              </h1>
              <p className="text-gray-600 mb-4">{profile.email}</p>
              <div className="flex gap-4">
                {profile.cv_data.linkedin && (
                  <a
                    href={`https://linkedin.com/in/${profile.cv_data.linkedin}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    LinkedIn
                  </a>
                )}
                {profile.cv_data.github && (
                  <a
                    href={`https://github.com/${profile.cv_data.github}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-gray-700 hover:underline"
                  >
                    GitHub
                  </a>
                )}
              </div>
              {isAdmin && (
                <div className="mt-4 inline-block bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm font-medium">
                  👑 Administrator
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Messages */}
        {message.text && (
          <div
            className={`mb-6 p-4 rounded-lg flex gap-3 ${
              message.type === 'success'
                ? 'bg-green-50 text-green-800'
                : 'bg-red-50 text-red-800'
            }`}
          >
            {message.type === 'success' ? (
              <CheckCircle size={20} className="flex-shrink-0 mt-0.5" />
            ) : (
              <AlertCircle size={20} className="flex-shrink-0 mt-0.5" />
            )}
            <span>{message.text}</span>
          </div>
        )}

        {/* Form Sections */}
        <div className="space-y-6">
          {/* Personal Data */}
          <div className="bg-white rounded-lg shadow-sm">
            <button
              onClick={() =>
                setExpandedSections(prev => ({
                  ...prev,
                  datosPersonales: !prev.datosPersonales
                }))
              }
              className="w-full px-6 py-4 font-semibold text-gray-900 hover:bg-gray-50 flex justify-between items-center"
            >
              Personal Data
              <span>{expandedSections.datosPersonales ? '▼' : '▶'}</span>
            </button>
            {expandedSections.datosPersonales && (
              <div className="px-6 py-4 border-t border-gray-200 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                    <input
                      type="text"
                      value={profile.cv_data.nombre || ''}
                      onChange={e => updateCVData('nombre', e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                    <input
                      type="email"
                      value={profile.cv_data.email || ''}
                      onChange={e => updateCVData('email', e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">LinkedIn</label>
                    <div className="flex items-center border border-gray-300 rounded-lg overflow-hidden">
                      <span className="px-3 py-2 bg-gray-100 text-gray-600 text-sm whitespace-nowrap">linkedin.com/in/</span>
                      <input
                        type="text"
                        value={profile.cv_data.linkedin || ''}
                        onChange={e => updateCVData('linkedin', e.target.value)}
                        className="flex-1 px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                        placeholder="username"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">GitHub</label>
                    <div className="flex items-center border border-gray-300 rounded-lg overflow-hidden">
                      <span className="px-3 py-2 bg-gray-100 text-gray-600 text-sm whitespace-nowrap">github.com/</span>
                      <input
                        type="text"
                        value={profile.cv_data.github || ''}
                        onChange={e => updateCVData('github', e.target.value)}
                        className="flex-1 px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
                        placeholder="username"
                      />
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                    <input
                      type="tel"
                      value={profile.cv_data.telefono || ''}
                      onChange={e => updateCVData('telefono', e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                    <input
                      type="text"
                      value={profile.cv_data.ubicacion || ''}
                      onChange={e => updateCVData('ubicacion', e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Website/Portfolio</label>
                    <input
                      type="url"
                      value={profile.cv_data.web || ''}
                      onChange={e => updateCVData('web', e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                  </div>
                </div>
                {isAdmin && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Telegram Chat ID (Admin only)</label>
                    <input
                      type="text"
                      value={profile.telegram_id || ''}
                      onChange={e => setProfile(prev => ({ ...prev, telegram_id: e.target.value }))}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Professional Summary */}
          <div className="bg-white rounded-lg shadow-sm">
            <button
              onClick={() =>
                setExpandedSections(prev => ({
                  ...prev,
                  resumen: !prev.resumen
                }))
              }
              className="w-full px-6 py-4 font-semibold text-gray-900 hover:bg-gray-50 flex justify-between items-center"
            >
              Professional Summary
              <span>{expandedSections.resumen ? '▼' : '▶'}</span>
            </button>
            {expandedSections.resumen && (
              <div className="px-6 py-4 border-t border-gray-200">
                <textarea
                  placeholder="Write your professional profile summary"
                  value={profile.cv_data.resumen_base || ''}
                  onChange={e => updateCVData('resumen_base', e.target.value)}
                  rows="5"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
            )}
          </div>

          {/* Skills */}
          <div className="bg-white rounded-lg shadow-sm">
            <button
              onClick={() =>
                setExpandedSections(prev => ({
                  ...prev,
                  habilidades: !prev.habilidades
                }))
              }
              className="w-full px-6 py-4 font-semibold text-gray-900 hover:bg-gray-50 flex justify-between items-center"
            >
              Skills
              <span>{expandedSections.habilidades ? '▼' : '▶'}</span>
            </button>
            {expandedSections.habilidades && (
              <div className="px-6 py-4 border-t border-gray-200 space-y-6">
                {Object.entries(profile.cv_data.habilidades_base || {}).map(([categoria, skills]) => (
                  <div key={categoria}>
                    <h4 className="font-medium text-gray-900 mb-2">{categoria}</h4>
                    <div className="flex flex-wrap gap-2 mb-3">
                      {skills.map((skill, idx) => (
                        <div
                          key={idx}
                          className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm flex items-center gap-2"
                        >
                          {skill}
                          <button
                            onClick={() => removeHabilidad(categoria, idx)}
                            className="hover:text-red-600"
                          >
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
                <div className="border-t border-gray-200 pt-4 space-y-3">
                  <h4 className="font-medium text-gray-900">Add New Skill</h4>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                      <input
                        type="text"
                        value={newSkillCategory}
                        onChange={(e) => setNewSkillCategory(e.target.value)}
                        placeholder="e.g., Programming"
                        list="skill-categories"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                      <datalist id="skill-categories">
                        {Object.keys(profile.cv_data.habilidades_base || {}).map((cat) => (
                          <option key={cat} value={cat} />
                        ))}
                      </datalist>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Skill Name</label>
                      <input
                        type="text"
                        value={newSkillName}
                        onChange={(e) => setNewSkillName(e.target.value)}
                        placeholder="e.g., React"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <div className="flex items-end">
                      <button
                        onClick={() => {
                          if (newSkillCategory && newSkillName) {
                            addHabilidad(newSkillCategory, newSkillName)
                            setNewSkillName('')
                            setNewSkillCategory('')
                          }
                        }}
                        disabled={!newSkillCategory || !newSkillName}
                        className="w-full bg-green-600 text-white py-2 rounded-lg font-medium hover:bg-green-700 disabled:bg-gray-400"
                      >
                        <Plus size={18} className="inline mr-1" />
                        Add
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Academic Education */}
          <div className="bg-white rounded-lg shadow-sm">
            <button
              onClick={() =>
                setExpandedSections(prev => ({
                  ...prev,
                  formacion: !prev.formacion
                }))
              }
              className="w-full px-6 py-4 font-semibold text-gray-900 hover:bg-gray-50 flex justify-between items-center"
            >
              Academic Education
              <span>{expandedSections.formacion ? '▼' : '▶'}</span>
            </button>
            {expandedSections.formacion && (
              <div className="px-6 py-4 border-t border-gray-200 space-y-4">
                {profile.cv_data.formacion.map((item, idx) => (
                  <div key={idx} className="border border-gray-200 rounded-lg p-4 space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Degree/Title</label>
                      <input
                        type="text"
                        value={item.titulo || ''}
                        onChange={e => updateFormacion(idx, 'titulo', e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Institution/School</label>
                      <input
                        type="text"
                        value={item.centro || ''}
                        onChange={e => updateFormacion(idx, 'centro', e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Year</label>
                      <input
                        type="text"
                        value={item.anio || ''}
                        onChange={e => updateFormacion(idx, 'anio', e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <button
                      onClick={() => removeFormacion(idx)}
                      className="text-red-600 hover:text-red-800 flex items-center gap-2"
                    >
                      <Trash2 size={18} /> Delete
                    </button>
                  </div>
                ))}
                <button
                  onClick={addFormacion}
                  className="w-full border-2 border-dashed border-gray-300 rounded-lg py-3 text-gray-600 hover:text-gray-900 hover:border-gray-400 flex items-center justify-center gap-2"
                >
                  <Plus size={20} /> Add Education
                </button>
              </div>
            )}
          </div>

          {/* Professional Experience */}
          <div className="bg-white rounded-lg shadow-sm">
            <button
              onClick={() =>
                setExpandedSections(prev => ({
                  ...prev,
                  experiencia: !prev.experiencia
                }))
              }
              className="w-full px-6 py-4 font-semibold text-gray-900 hover:bg-gray-50 flex justify-between items-center"
            >
              Professional Experience
              <span>{expandedSections.experiencia ? '▼' : '▶'}</span>
            </button>
            {expandedSections.experiencia && (
              <div className="px-6 py-4 border-t border-gray-200 space-y-4">
                {profile.cv_data.experiencia_base.map((item, idx) => (
                  <div key={idx} className="border border-gray-200 rounded-lg p-4 space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Job Title</label>
                      <input
                        type="text"
                        value={item.puesto || ''}
                        onChange={e => updateExperiencia(idx, 'puesto', e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Company</label>
                      <input
                        type="text"
                        value={item.empresa || ''}
                        onChange={e => updateExperiencia(idx, 'empresa', e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Duration</label>
                      <input
                        type="text"
                        value={item.duracion || ''}
                        onChange={e => updateExperiencia(idx, 'duracion', e.target.value)}
                        placeholder="e.g., 2023-2024"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Quantifiable Impact</label>
                      <input
                        type="text"
                        value={item.impacto || ''}
                        onChange={e => updateExperiencia(idx, 'impacto', e.target.value)}
                        placeholder="e.g., Reduced time by 40%"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <button
                      onClick={() => removeExperiencia(idx)}
                      className="text-red-600 hover:text-red-800 flex items-center gap-2"
                    >
                      <Trash2 size={18} /> Delete
                    </button>
                  </div>
                ))}
                <button
                  onClick={addExperiencia}
                  className="w-full border-2 border-dashed border-gray-300 rounded-lg py-3 text-gray-600 hover:text-gray-900 hover:border-gray-400 flex items-center justify-center gap-2"
                >
                  <Plus size={20} /> Add Experience
                </button>
              </div>
            )}
          </div>

          {/* Featured Projects */}
          <div className="bg-white rounded-lg shadow-sm">
            <button
              onClick={() =>
                setExpandedSections(prev => ({
                  ...prev,
                  proyectos: !prev.proyectos
                }))
              }
              className="w-full px-6 py-4 font-semibold text-gray-900 hover:bg-gray-50 flex justify-between items-center"
            >
              Featured Projects
              <span>{expandedSections.proyectos ? '▼' : '▶'}</span>
            </button>
            {expandedSections.proyectos && (
              <div className="px-6 py-4 border-t border-gray-200 space-y-4">
                {profile.cv_data.proyectos.map((item, idx) => (
                  <div key={idx} className="border border-gray-200 rounded-lg p-4 space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Project Name</label>
                      <input
                        type="text"
                        value={item.nombre || ''}
                        onChange={e => updateProyecto(idx, 'nombre', e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                      <textarea
                        value={item.descripcion || ''}
                        onChange={e => updateProyecto(idx, 'descripcion', e.target.value)}
                        rows="3"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <button
                      onClick={() => removeProyecto(idx)}
                      className="text-red-600 hover:text-red-800 flex items-center gap-2"
                    >
                      <Trash2 size={18} /> Delete
                    </button>
                  </div>
                ))}
                <button
                  onClick={addProyecto}
                  className="w-full border-2 border-dashed border-gray-300 rounded-lg py-3 text-gray-600 hover:text-gray-900 hover:border-gray-400 flex items-center justify-center gap-2"
                >
                  <Plus size={20} /> Add Project
                </button>
              </div>
            )}
          </div>

          {/* Languages */}
          <div className="bg-white rounded-lg shadow-sm">
            <button
              onClick={() =>
                setExpandedSections(prev => ({
                  ...prev,
                  idiomas: !prev.idiomas
                }))
              }
              className="w-full px-6 py-4 font-semibold text-gray-900 hover:bg-gray-50 flex justify-between items-center"
            >
              Languages
              <span>{expandedSections.idiomas ? '▼' : '▶'}</span>
            </button>
            {expandedSections.idiomas && (
              <div className="px-6 py-4 border-t border-gray-200 space-y-4">
                {profile.cv_data.idiomas.map((item, idx) => (
                  <div key={idx} className="border border-gray-200 rounded-lg p-4 space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Language</label>
                      <input
                        type="text"
                        value={item.idioma || ''}
                        onChange={e => updateIdioma(idx, 'idioma', e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Level</label>
                      <input
                        type="text"
                        value={item.nivel || ''}
                        onChange={e => updateIdioma(idx, 'nivel', e.target.value)}
                        placeholder="e.g. Nativo, C1, Profesional..."
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <button
                      onClick={() => removeIdioma(idx)}
                      className="text-red-600 hover:text-red-800 flex items-center gap-2"
                    >
                      <Trash2 size={18} /> Delete
                    </button>
                  </div>
                ))}
                <button
                  onClick={addIdioma}
                  className="w-full border-2 border-dashed border-gray-300 rounded-lg py-3 text-gray-600 hover:text-gray-900 hover:border-gray-400 flex items-center justify-center gap-2"
                >
                  <Plus size={20} /> Add Language
                </button>
              </div>
            )}
          </div>

          {/* Certifications */}
          <div className="bg-white rounded-lg shadow-sm">
            <button
              onClick={() =>
                setExpandedSections(prev => ({
                  ...prev,
                  certificaciones: !prev.certificaciones
                }))
              }
              className="w-full px-6 py-4 font-semibold text-gray-900 hover:bg-gray-50 flex justify-between items-center"
            >
              Certifications
              <span>{expandedSections.certificaciones ? '▼' : '▶'}</span>
            </button>
            {expandedSections.certificaciones && (
              <div className="px-6 py-4 border-t border-gray-200 space-y-4">
                {profile.cv_data.certificaciones.map((item, idx) => (
                  <div key={idx} className="border border-gray-200 rounded-lg p-4 space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Certification Name</label>
                      <input
                        type="text"
                        value={item.nombre || ''}
                        onChange={e => updateCertificacion(idx, 'nombre', e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Issuing Organization</label>
                      <input
                        type="text"
                        value={item.emisor || ''}
                        onChange={e => updateCertificacion(idx, 'emisor', e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Year</label>
                      <input
                        type="text"
                        value={item.anio || ''}
                        onChange={e => updateCertificacion(idx, 'anio', e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <button
                      onClick={() => removeCertificacion(idx)}
                      className="text-red-600 hover:text-red-800 flex items-center gap-2"
                    >
                      <Trash2 size={18} /> Delete
                    </button>
                  </div>
                ))}
                <button
                  onClick={addCertificacion}
                  className="w-full border-2 border-dashed border-gray-300 rounded-lg py-3 text-gray-600 hover:text-gray-900 hover:border-gray-400 flex items-center justify-center gap-2"
                >
                  <Plus size={20} /> Add Certification
                </button>
              </div>
            )}
          </div>

          {/* Courses */}
          <div className="bg-white rounded-lg shadow-sm">
            <button
              onClick={() =>
                setExpandedSections(prev => ({
                  ...prev,
                  cursos: !prev.cursos
                }))
              }
              className="w-full px-6 py-4 font-semibold text-gray-900 hover:bg-gray-50 flex justify-between items-center"
            >
              Courses
              <span>{expandedSections.cursos ? '▼' : '▶'}</span>
            </button>
            {expandedSections.cursos && (
              <div className="px-6 py-4 border-t border-gray-200 space-y-4">
                {profile.cv_data.cursos.map((item, idx) => (
                  <div key={idx} className="border border-gray-200 rounded-lg p-4 space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Course Name</label>
                      <input
                        type="text"
                        value={item.nombre || ''}
                        onChange={e => updateCurso(idx, 'nombre', e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Platform</label>
                      <input
                        type="text"
                        value={item.plataforma || ''}
                        onChange={e => updateCurso(idx, 'plataforma', e.target.value)}
                        placeholder="e.g., Coursera, Udemy"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Year</label>
                      <input
                        type="text"
                        value={item.anio || ''}
                        onChange={e => updateCurso(idx, 'anio', e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <button
                      onClick={() => removeCurso(idx)}
                      className="text-red-600 hover:text-red-800 flex items-center gap-2"
                    >
                      <Trash2 size={18} /> Delete
                    </button>
                  </div>
                ))}
                <button
                  onClick={addCurso}
                  className="w-full border-2 border-dashed border-gray-300 rounded-lg py-3 text-gray-600 hover:text-gray-900 hover:border-gray-400 flex items-center justify-center gap-2"
                >
                  <Plus size={20} /> Add Course
                </button>
              </div>
            )}
          </div>

          {/* Volunteering */}
          <div className="bg-white rounded-lg shadow-sm">
            <button
              onClick={() =>
                setExpandedSections(prev => ({
                  ...prev,
                  voluntariado: !prev.voluntariado
                }))
              }
              className="w-full px-6 py-4 font-semibold text-gray-900 hover:bg-gray-50 flex justify-between items-center"
            >
              Volunteering
              <span>{expandedSections.voluntariado ? '▼' : '▶'}</span>
            </button>
            {expandedSections.voluntariado && (
              <div className="px-6 py-4 border-t border-gray-200 space-y-4">
                {profile.cv_data.voluntariado.map((item, idx) => (
                  <div key={idx} className="border border-gray-200 rounded-lg p-4 space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Organization</label>
                      <input
                        type="text"
                        value={item.organizacion || ''}
                        onChange={e => updateVoluntariado(idx, 'organizacion', e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                      <input
                        type="text"
                        value={item.rol || ''}
                        onChange={e => updateVoluntariado(idx, 'rol', e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Description of Activities</label>
                      <textarea
                        value={item.descripcion || ''}
                        onChange={e => updateVoluntariado(idx, 'descripcion', e.target.value)}
                        rows="3"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Year</label>
                      <input
                        type="text"
                        value={item.anio || ''}
                        onChange={e => updateVoluntariado(idx, 'anio', e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                    </div>
                    <button
                      onClick={() => removeVoluntariado(idx)}
                      className="text-red-600 hover:text-red-800 flex items-center gap-2"
                    >
                      <Trash2 size={18} /> Delete
                    </button>
                  </div>
                ))}
                <button
                  onClick={addVoluntariado}
                  className="w-full border-2 border-dashed border-gray-300 rounded-lg py-3 text-gray-600 hover:text-gray-900 hover:border-gray-400 flex items-center justify-center gap-2"
                >
                  <Plus size={20} /> Add Volunteering
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Save Button */}
        <div className="mt-8 flex gap-4">
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex-1 bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 flex items-center justify-center gap-2"
          >
            <Save size={20} />
            {saving ? 'Saving...' : 'Save Profile'}
          </button>
        </div>
      </div>
    </Layout>
  )
}
