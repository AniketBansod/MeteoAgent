import { useState } from 'react'
import { sendChat } from '../api/chat.js'

export function useChat(){
  const [messages,setMessages] = useState([])
  const [loading,setLoading] = useState(false)
  const [error,setError] = useState(null)

  const append = (role,text)=> setMessages(m=>[...m,{role,text,ts:Date.now()}])

  const send = async (text)=>{
    setError(null); append('user', text); setLoading(true)
    try{ const res = await sendChat(text); append('assistant', res?.answer ?? ''); }
    catch(e){ setError('Failed'); append('assistant','Sorry, there was an error.') }
    finally{ setLoading(false) }
  }

  return {messages,loading,error,send}
}
