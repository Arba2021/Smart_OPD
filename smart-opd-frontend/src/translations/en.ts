import { Translation } from '@/types'

const en: Translation = {
  common: {
    loading: 'Processing your request...',
    error: 'An error occurred',
    submit: 'Proceed',
    cancel: 'Cancel',
    close: 'Close',
    phone: 'Mobile Number',
    name: 'Patient Full Name',
    symptom: 'Primary Symptom',
    doctor: 'Select Department',
    token: 'Token',
    status: 'Status',
    wait: 'Estimated Wait',
    patientsAhead: 'Patients Ahead',
    sms: 'SMS Notifications',
    language: 'Language',
  },
  booking: {
    title: 'Smart OPD Booking',
    subtitle: 'AI-powered triage and queue management',
    placeholder: {
      name: 'Enter full name',
      phone: '10-digit mobile number',
      symptom: 'e.g. Fever, Joint Pain',
    },
    hint: {
      phone: 'We will send an SMS to this number.',
      symptom: 'Helps AI prioritize your case.',
    },
    button: 'Generate Token',
    success: {
      title: 'Token Confirmed',
      message: 'Your appointment is booked. Please wait for SMS instructions before traveling.',
    },
  },
  status: {
    title: 'Track Token Status',
    subtitle: 'Enter your mobile number to view queue position',
    placeholder: '10-digit mobile number',
    button: 'Track Token',
    notFound: 'No active token found for this number today.',
    waiting: 'Waiting in Queue',
    called: 'Proceed to Doctor Room',
    inRoom: 'In Consultation',
    instruction: {
      waiting: 'Do not travel to the hospital yet. We will alert you via SMS when it is time to leave.',
      called: 'Please proceed to the doctor room immediately. Show this token at the entrance.',
    },
  },
  sms: {
    title: 'SMS Communication Log',
    subtitle: 'Real-time patient messaging',
    empty: 'No messages sent yet.',
    demo: 'MOCK DEVICE: DEMO MODE',
  },
  triage: {
    red: 'RED',
    yellow: 'YELLOW',
    green: 'GREEN',
    priority: 'PRIORITY',
  },
}

export default en