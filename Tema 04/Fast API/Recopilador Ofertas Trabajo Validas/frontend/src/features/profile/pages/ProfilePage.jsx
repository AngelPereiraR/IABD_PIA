import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, Plus, Trash2, Save, AlertCircle, CheckCircle } from 'lucide-react'
import { profileService } from '../../../services/profileService'
import Layout from '../../../shared/components/Layout'

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
        text: 'Error al cargar el perfil: ' + (error.response?.data?.detail || error.message)
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
      setMessage({ type: 'success', text: 'Foto de perfil actualizada' })
      setTimeout(() => setMessage({ type: '', text: '' }), 3000)
    } catch (error) {
      setMessage({
        type: 'error',
        text: 'Error al subir foto: ' + (error.response?.data?.detail || error.message)
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
    setProfile(prev => ({
      ...prev,
      cv_data: {
        ...prev.cv_data,
        habilidades_base: {
          ...prev.cv_data.habilidades_base,
          [categoria]: prev.cv_data.habilidades_base[categoria].filter((_, i) => i !== index)
        }
      }
    }))
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      const updateData = { cv_data: profile.cv_data }

      // Solo agregar telegram_id si es admin y cambió
      if (isAdmin && profile.telegram_id) {
        updateData.telegram_id = profile.telegram_id
      }

      await profileService.updateProfile(updateData)
      setMessage({ type: 'success', text: 'Perfil guardado correctamente' })
      setTimeout(() => setMessage({ type: '', text: '' }), 3000)
    } catch (error) {
      const detail = error.response?.data?.detail
      if (detail && detail.includes('admin')) {
        setMessage({ type: 'error', text: 'No tienes permiso para actualizar telegram_id' })
      } else {
        setMessage({ type: 'error', text: 'Error al guardar: ' + (detail || error.message) })
      }
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <Layout>
        <div className="flex justify-center items-center h-64">
          <div className="text-gray-500">Cargando perfil...</div>
        </div>
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
                {profile.cv_data.nombre || 'Sin nombre'}
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
                  👑 Administrador
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
          {/* Datos Personales */}
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
              Datos Personales
              <span>{expandedSections.datosPersonales ? '▼' : '▶'}</span>
            </button>
            {expandedSections.datosPersonales && (
              <div className="px-6 py-4 border-t border-gray-200 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <input
                    type="text"
                    placeholder="Nombre completo"
                    value={profile.cv_data.nombre || ''}
                    onChange={e => updateCVData('nombre', e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                  <input
                    type="email"
                    placeholder="Email"
                    value={profile.cv_data.email || ''}
                    onChange={e => updateCVData('email', e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <input
                    type="text"
                    placeholder="LinkedIn (usuario)"
                    value={profile.cv_data.linkedin || ''}
                    onChange={e => updateCVData('linkedin', e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                  <input
                    type="text"
                    placeholder="GitHub (usuario)"
                    value={profile.cv_data.github || ''}
                    onChange={e => updateCVData('github', e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <input
                    type="tel"
                    placeholder="Teléfono"
                    value={profile.cv_data.telefono || ''}
                    onChange={e => updateCVData('telefono', e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                  <input
                    type="text"
                    placeholder="Ubicación"
                    value={profile.cv_data.ubicacion || ''}
                    onChange={e => updateCVData('ubicacion', e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                  <input
                    type="url"
                    placeholder="Website/Portfolio"
                    value={profile.cv_data.web || ''}
                    onChange={e => updateCVData('web', e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>
                {isAdmin && (
                  <input
                    type="text"
                    placeholder="Telegram Chat ID (solo admin)"
                    value={profile.telegram_id || ''}
                    onChange={e => setProfile(prev => ({ ...prev, telegram_id: e.target.value }))}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                )}
              </div>
            )}
          </div>

          {/* Resumen */}
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
              Resumen Profesional
              <span>{expandedSections.resumen ? '▼' : '▶'}</span>
            </button>
            {expandedSections.resumen && (
              <div className="px-6 py-4 border-t border-gray-200">
                <textarea
                  placeholder="Resumen de tu perfil profesional"
                  value={profile.cv_data.resumen_base || ''}
                  onChange={e => updateCVData('resumen_base', e.target.value)}
                  rows="5"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
            )}
          </div>

          {/* Habilidades */}
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
              Habilidades
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
              </div>
            )}
          </div>

          {/* Formación */}
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
              Formación Académica
              <span>{expandedSections.formacion ? '▼' : '▶'}</span>
            </button>
            {expandedSections.formacion && (
              <div className="px-6 py-4 border-t border-gray-200 space-y-4">
                {profile.cv_data.formacion.map((item, idx) => (
                  <div key={idx} className="border border-gray-200 rounded-lg p-4 space-y-3">
                    <input
                      type="text"
                      placeholder="Título"
                      value={item.titulo || ''}
                      onChange={e => updateFormacion(idx, 'titulo', e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                    <input
                      type="text"
                      placeholder="Centro educativo"
                      value={item.centro || ''}
                      onChange={e => updateFormacion(idx, 'centro', e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                    <input
                      type="text"
                      placeholder="Año"
                      value={item.anio || ''}
                      onChange={e => updateFormacion(idx, 'anio', e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                    <button
                      onClick={() => removeFormacion(idx)}
                      className="text-red-600 hover:text-red-800 flex items-center gap-2"
                    >
                      <Trash2 size={18} /> Eliminar
                    </button>
                  </div>
                ))}
                <button
                  onClick={addFormacion}
                  className="w-full border-2 border-dashed border-gray-300 rounded-lg py-3 text-gray-600 hover:text-gray-900 hover:border-gray-400 flex items-center justify-center gap-2"
                >
                  <Plus size={20} /> Agregar formación
                </button>
              </div>
            )}
          </div>

          {/* Experiencia */}
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
              Experiencia Profesional
              <span>{expandedSections.experiencia ? '▼' : '▶'}</span>
            </button>
            {expandedSections.experiencia && (
              <div className="px-6 py-4 border-t border-gray-200 space-y-4">
                {profile.cv_data.experiencia_base.map((item, idx) => (
                  <div key={idx} className="border border-gray-200 rounded-lg p-4 space-y-3">
                    <input
                      type="text"
                      placeholder="Puesto"
                      value={item.puesto || ''}
                      onChange={e => updateExperiencia(idx, 'puesto', e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                    <input
                      type="text"
                      placeholder="Empresa"
                      value={item.empresa || ''}
                      onChange={e => updateExperiencia(idx, 'empresa', e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                    <input
                      type="text"
                      placeholder="Duración (ej: 2023-2024)"
                      value={item.duracion || ''}
                      onChange={e => updateExperiencia(idx, 'duracion', e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                    <input
                      type="text"
                      placeholder="Impacto cuantificable (ej: Redujo tiempo un 40%)"
                      value={item.impacto || ''}
                      onChange={e => updateExperiencia(idx, 'impacto', e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                    <button
                      onClick={() => removeExperiencia(idx)}
                      className="text-red-600 hover:text-red-800 flex items-center gap-2"
                    >
                      <Trash2 size={18} /> Eliminar
                    </button>
                  </div>
                ))}
                <button
                  onClick={addExperiencia}
                  className="w-full border-2 border-dashed border-gray-300 rounded-lg py-3 text-gray-600 hover:text-gray-900 hover:border-gray-400 flex items-center justify-center gap-2"
                >
                  <Plus size={20} /> Agregar experiencia
                </button>
              </div>
            )}
          </div>

          {/* Proyectos */}
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
              Proyectos Destacados
              <span>{expandedSections.proyectos ? '▼' : '▶'}</span>
            </button>
            {expandedSections.proyectos && (
              <div className="px-6 py-4 border-t border-gray-200 space-y-4">
                {profile.cv_data.proyectos.map((item, idx) => (
                  <div key={idx} className="border border-gray-200 rounded-lg p-4 space-y-3">
                    <input
                      type="text"
                      placeholder="Nombre del proyecto"
                      value={item.nombre || ''}
                      onChange={e => updateProyecto(idx, 'nombre', e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                    <textarea
                      placeholder="Descripción"
                      value={item.descripcion || ''}
                      onChange={e => updateProyecto(idx, 'descripcion', e.target.value)}
                      rows="3"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                    <button
                      onClick={() => removeProyecto(idx)}
                      className="text-red-600 hover:text-red-800 flex items-center gap-2"
                    >
                      <Trash2 size={18} /> Eliminar
                    </button>
                  </div>
                ))}
                <button
                  onClick={addProyecto}
                  className="w-full border-2 border-dashed border-gray-300 rounded-lg py-3 text-gray-600 hover:text-gray-900 hover:border-gray-400 flex items-center justify-center gap-2"
                >
                  <Plus size={20} /> Agregar proyecto
                </button>
              </div>
            )}
          </div>

          {/* Idiomas */}
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
              Idiomas
              <span>{expandedSections.idiomas ? '▼' : '▶'}</span>
            </button>
            {expandedSections.idiomas && (
              <div className="px-6 py-4 border-t border-gray-200 space-y-4">
                {profile.cv_data.idiomas.map((item, idx) => (
                  <div key={idx} className="border border-gray-200 rounded-lg p-4 space-y-3">
                    <input
                      type="text"
                      placeholder="Idioma"
                      value={item.idioma || ''}
                      onChange={e => updateIdioma(idx, 'idioma', e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                    <select
                      value={item.nivel || ''}
                      onChange={e => updateIdioma(idx, 'nivel', e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    >
                      <option value="">Seleccionar nivel</option>
                      <option value="nativo">Nativo</option>
                      <option value="fluido">Fluido</option>
                      <option value="intermedio">Intermedio</option>
                      <option value="básico">Básico</option>
                    </select>
                    <button
                      onClick={() => removeIdioma(idx)}
                      className="text-red-600 hover:text-red-800 flex items-center gap-2"
                    >
                      <Trash2 size={18} /> Eliminar
                    </button>
                  </div>
                ))}
                <button
                  onClick={addIdioma}
                  className="w-full border-2 border-dashed border-gray-300 rounded-lg py-3 text-gray-600 hover:text-gray-900 hover:border-gray-400 flex items-center justify-center gap-2"
                >
                  <Plus size={20} /> Agregar idioma
                </button>
              </div>
            )}
          </div>

          {/* Certificaciones */}
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
              Certificaciones
              <span>{expandedSections.certificaciones ? '▼' : '▶'}</span>
            </button>
            {expandedSections.certificaciones && (
              <div className="px-6 py-4 border-t border-gray-200 space-y-4">
                {profile.cv_data.certificaciones.map((item, idx) => (
                  <div key={idx} className="border border-gray-200 rounded-lg p-4 space-y-3">
                    <input
                      type="text"
                      placeholder="Nombre de la certificación"
                      value={item.nombre || ''}
                      onChange={e => updateCertificacion(idx, 'nombre', e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                    <input
                      type="text"
                      placeholder="Entidad emisora"
                      value={item.emisor || ''}
                      onChange={e => updateCertificacion(idx, 'emisor', e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                    <input
                      type="text"
                      placeholder="Año"
                      value={item.anio || ''}
                      onChange={e => updateCertificacion(idx, 'anio', e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                    <button
                      onClick={() => removeCertificacion(idx)}
                      className="text-red-600 hover:text-red-800 flex items-center gap-2"
                    >
                      <Trash2 size={18} /> Eliminar
                    </button>
                  </div>
                ))}
                <button
                  onClick={addCertificacion}
                  className="w-full border-2 border-dashed border-gray-300 rounded-lg py-3 text-gray-600 hover:text-gray-900 hover:border-gray-400 flex items-center justify-center gap-2"
                >
                  <Plus size={20} /> Agregar certificación
                </button>
              </div>
            )}
          </div>

          {/* Cursos */}
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
              Cursos
              <span>{expandedSections.cursos ? '▼' : '▶'}</span>
            </button>
            {expandedSections.cursos && (
              <div className="px-6 py-4 border-t border-gray-200 space-y-4">
                {profile.cv_data.cursos.map((item, idx) => (
                  <div key={idx} className="border border-gray-200 rounded-lg p-4 space-y-3">
                    <input
                      type="text"
                      placeholder="Nombre del curso"
                      value={item.nombre || ''}
                      onChange={e => updateCurso(idx, 'nombre', e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                    <input
                      type="text"
                      placeholder="Plataforma (Coursera, Udemy, etc.)"
                      value={item.plataforma || ''}
                      onChange={e => updateCurso(idx, 'plataforma', e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                    <input
                      type="text"
                      placeholder="Año"
                      value={item.anio || ''}
                      onChange={e => updateCurso(idx, 'anio', e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                    <button
                      onClick={() => removeCurso(idx)}
                      className="text-red-600 hover:text-red-800 flex items-center gap-2"
                    >
                      <Trash2 size={18} /> Eliminar
                    </button>
                  </div>
                ))}
                <button
                  onClick={addCurso}
                  className="w-full border-2 border-dashed border-gray-300 rounded-lg py-3 text-gray-600 hover:text-gray-900 hover:border-gray-400 flex items-center justify-center gap-2"
                >
                  <Plus size={20} /> Agregar curso
                </button>
              </div>
            )}
          </div>

          {/* Voluntariado */}
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
              Voluntariado
              <span>{expandedSections.voluntariado ? '▼' : '▶'}</span>
            </button>
            {expandedSections.voluntariado && (
              <div className="px-6 py-4 border-t border-gray-200 space-y-4">
                {profile.cv_data.voluntariado.map((item, idx) => (
                  <div key={idx} className="border border-gray-200 rounded-lg p-4 space-y-3">
                    <input
                      type="text"
                      placeholder="Organización"
                      value={item.organizacion || ''}
                      onChange={e => updateVoluntariado(idx, 'organizacion', e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                    <input
                      type="text"
                      placeholder="Rol"
                      value={item.rol || ''}
                      onChange={e => updateVoluntariado(idx, 'rol', e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                    <textarea
                      placeholder="Descripción de actividades"
                      value={item.descripcion || ''}
                      onChange={e => updateVoluntariado(idx, 'descripcion', e.target.value)}
                      rows="3"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                    <input
                      type="text"
                      placeholder="Año"
                      value={item.anio || ''}
                      onChange={e => updateVoluntariado(idx, 'anio', e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    />
                    <button
                      onClick={() => removeVoluntariado(idx)}
                      className="text-red-600 hover:text-red-800 flex items-center gap-2"
                    >
                      <Trash2 size={18} /> Eliminar
                    </button>
                  </div>
                ))}
                <button
                  onClick={addVoluntariado}
                  className="w-full border-2 border-dashed border-gray-300 rounded-lg py-3 text-gray-600 hover:text-gray-900 hover:border-gray-400 flex items-center justify-center gap-2"
                >
                  <Plus size={20} /> Agregar voluntariado
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
            {saving ? 'Guardando...' : 'Guardar perfil'}
          </button>
        </div>
      </div>
    </Layout>
  )
}
