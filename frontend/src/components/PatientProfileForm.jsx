import React, { useState } from 'react'
import './PatientProfileForm.css'

const COMMON_CONDITIONS = [
  'Diabetes',
  'Hypertension (High Blood Pressure)',
  'Cancer',
  'Heart Disease',
  'Asthma',
  'COPD (Chronic Obstructive Pulmonary Disease)',
  'Arthritis',
  'Depression',
  'Anxiety',
  'Alzheimer\'s Disease',
  'Parkinson\'s Disease',
  'Kidney Disease',
  'Liver Disease',
  'Stroke',
  'Other (specify below)'
]

const PatientProfileForm = ({ onSubmit, isLoading }) => {
  const [formData, setFormData] = useState({
    condition: '',
    customCondition: '',
    age: '',
    gender: '',
    location: '',
    distanceMiles: 50,
    medicalHistory: ''
  })

  const [errors, setErrors] = useState({})

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }))
    }
  }

  const validateForm = () => {
    const newErrors = {}

    // Condition validation
    if (!formData.condition) {
      newErrors.condition = 'Please select a medical condition'
    } else if (formData.condition === 'Other (specify below)' && !formData.customCondition.trim()) {
      newErrors.customCondition = 'Please specify your condition'
    }

    // Age validation
    if (!formData.age) {
      newErrors.age = 'Please enter your age'
    } else {
      const age = parseInt(formData.age)
      if (isNaN(age) || age < 0 || age > 120) {
        newErrors.age = 'Please enter a valid age between 0 and 120'
      }
    }

    // Gender validation
    if (!formData.gender) {
      newErrors.gender = 'Please select your gender'
    }

    // Location validation
    if (!formData.location.trim()) {
      newErrors.location = 'Please enter your location'
    }

    // Medical history validation
    if (!formData.medicalHistory.trim()) {
      newErrors.medicalHistory = 'Please provide your medical history'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    if (validateForm()) {
      const finalCondition = formData.condition === 'Other (specify below)' 
        ? formData.customCondition 
        : formData.condition

      onSubmit({
        condition: finalCondition,
        age: parseInt(formData.age),
        gender: formData.gender,
        location: formData.location,
        distance_miles: parseInt(formData.distanceMiles),
        medical_history: formData.medicalHistory
      })
    }
  }

  return (
    <form className="patient-profile-form" onSubmit={handleSubmit} noValidate>
      <div className="form-header">
        <h1>Find Your Clinical Trial Match</h1>
        <p>Enter your information to find trials that match your profile</p>
      </div>

      {/* Medical Condition Section */}
      <section className="form-section">
        <h2>Medical Condition</h2>
        
        <div className="form-group">
          <label htmlFor="condition">
            Primary Condition <span className="required" aria-label="required">*</span>
          </label>
          <select
            id="condition"
            name="condition"
            value={formData.condition}
            onChange={handleChange}
            className={errors.condition ? 'error' : ''}
            disabled={isLoading}
            aria-required="true"
            aria-invalid={errors.condition ? 'true' : 'false'}
            aria-describedby={errors.condition ? 'condition-error' : undefined}
          >
            <option value="">Select a condition...</option>
            {COMMON_CONDITIONS.map(condition => (
              <option key={condition} value={condition}>{condition}</option>
            ))}
          </select>
          {errors.condition && (
            <span id="condition-error" className="error-message" role="alert">
              {errors.condition}
            </span>
          )}
        </div>

        {formData.condition === 'Other (specify below)' && (
          <div className="form-group">
            <label htmlFor="customCondition">
              Specify Your Condition <span className="required" aria-label="required">*</span>
            </label>
            <input
              type="text"
              id="customCondition"
              name="customCondition"
              value={formData.customCondition}
              onChange={handleChange}
              placeholder="e.g., Rheumatoid Arthritis"
              className={errors.customCondition ? 'error' : ''}
              disabled={isLoading}
              aria-required="true"
              aria-invalid={errors.customCondition ? 'true' : 'false'}
              aria-describedby={errors.customCondition ? 'customCondition-error' : undefined}
            />
            {errors.customCondition && (
              <span id="customCondition-error" className="error-message" role="alert">
                {errors.customCondition}
              </span>
            )}
          </div>
        )}
      </section>

      {/* Demographics Section */}
      <section className="form-section">
        <h2>Demographics</h2>
        
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="age">
              Age <span className="required" aria-label="required">*</span>
            </label>
            <input
              type="number"
              id="age"
              name="age"
              value={formData.age}
              onChange={handleChange}
              placeholder="Enter your age"
              min="0"
              max="120"
              className={errors.age ? 'error' : ''}
              disabled={isLoading}
              aria-required="true"
              aria-invalid={errors.age ? 'true' : 'false'}
              aria-describedby={errors.age ? 'age-error' : undefined}
            />
            {errors.age && (
              <span id="age-error" className="error-message" role="alert">
                {errors.age}
              </span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="gender">
              Gender <span className="required" aria-label="required">*</span>
            </label>
            <div className="radio-group" role="radiogroup" aria-labelledby="gender" aria-required="true">
              {['Male', 'Female', 'Other', 'Prefer not to say'].map(option => (
                <label key={option} className="radio-label">
                  <input
                    type="radio"
                    name="gender"
                    value={option}
                    checked={formData.gender === option}
                    onChange={handleChange}
                    disabled={isLoading}
                    aria-checked={formData.gender === option}
                  />
                  <span>{option}</span>
                </label>
              ))}
            </div>
            {errors.gender && (
              <span id="gender-error" className="error-message" role="alert">
                {errors.gender}
              </span>
            )}
          </div>
        </div>
      </section>

      {/* Location Section */}
      <section className="form-section">
        <h2>Location</h2>
        
        <div className="form-group">
          <label htmlFor="location">
            City or State <span className="required" aria-label="required">*</span>
          </label>
          <input
            type="text"
            id="location"
            name="location"
            value={formData.location}
            onChange={handleChange}
            placeholder="e.g., New York, NY or Boston"
            className={errors.location ? 'error' : ''}
            disabled={isLoading}
            aria-required="true"
            aria-invalid={errors.location ? 'true' : 'false'}
            aria-describedby={errors.location ? 'location-error location-help' : 'location-help'}
          />
          <span id="location-help" className="help-text">
            Enter your city and state or just your city name
          </span>
          {errors.location && (
            <span id="location-error" className="error-message" role="alert">
              {errors.location}
            </span>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="distanceMiles">
            Search Radius: {formData.distanceMiles} miles
          </label>
          <input
            type="range"
            id="distanceMiles"
            name="distanceMiles"
            min="10"
            max="500"
            step="10"
            value={formData.distanceMiles}
            onChange={handleChange}
            disabled={isLoading}
            aria-valuemin="10"
            aria-valuemax="500"
            aria-valuenow={formData.distanceMiles}
            aria-label={`Search radius: ${formData.distanceMiles} miles`}
          />
          <div className="slider-labels">
            <span>10 miles</span>
            <span>500 miles</span>
          </div>
        </div>
      </section>

      {/* Medical History Section */}
      <section className="form-section">
        <h2>Medical History</h2>
        
        <div className="form-group">
          <label htmlFor="medicalHistory">
            Medical History <span className="required" aria-label="required">*</span>
          </label>
          <textarea
            id="medicalHistory"
            name="medicalHistory"
            value={formData.medicalHistory}
            onChange={handleChange}
            placeholder="Please describe your medical history, including:&#10;• Chronic conditions&#10;• Current medications&#10;• Previous treatments&#10;• Allergies&#10;• Recent surgeries or procedures"
            rows="6"
            className={errors.medicalHistory ? 'error' : ''}
            disabled={isLoading}
            aria-required="true"
            aria-invalid={errors.medicalHistory ? 'true' : 'false'}
            aria-describedby={errors.medicalHistory ? 'medicalHistory-error medicalHistory-help' : 'medicalHistory-help'}
          />
          <span id="medicalHistory-help" className="help-text">
            Provide as much detail as possible to help us find the best matches
          </span>
          {errors.medicalHistory && (
            <span id="medicalHistory-error" className="error-message" role="alert">
              {errors.medicalHistory}
            </span>
          )}
        </div>
      </section>

      <div className="form-actions">
        <button 
          type="submit" 
          className="submit-button"
          disabled={isLoading}
          aria-busy={isLoading}
        >
          {isLoading ? 'Searching...' : 'Find Matching Trials'}
        </button>
      </div>
    </form>
  )
}

export default PatientProfileForm
