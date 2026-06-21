import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

export default function CheckoutPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', address: '' })
  const [ordered, setOrdered] = useState(null)
  const sessionId = localStorage.getItem('session_id')

  const placeOrder = async (e) => {
    e.preventDefault()
    try {
      const r = await axios.post(`/v1/cart/${sessionId}/checkout`, { shipping_address: form.address })
      setOrdered(r.data)
    } catch (err) {
      alert(err.response?.data?.detail || 'Checkout failed')
    }
  }

  if (ordered) return (
    <div className="max-w-lg mx-auto px-4 py-16 text-center">
      <div className="text-5xl mb-4">✅</div>
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Order Placed!</h1>
      <p className="text-gray-500 text-sm mb-1">Order ID: <span className="font-mono text-xs">{ordered.order_id}</span></p>
      <p className="text-indigo-600 font-bold text-lg mb-6">Total: £{Number(ordered.total).toFixed(2)}</p>
      <button onClick={() => navigate('/')} className="bg-indigo-600 text-white px-8 py-2 rounded-lg hover:bg-indigo-700">Continue Shopping</button>
    </div>
  )

  return (
    <div className="max-w-lg mx-auto px-4 py-10">
      <h1 className="text-2xl font-bold text-gray-900 mb-8">Checkout</h1>
      <form onSubmit={placeOrder} className="bg-white rounded-xl border border-gray-100 p-6 space-y-4">
        <div>
          <label className="text-sm text-gray-600 block mb-1">Full Name</label>
          <input required value={form.name} onChange={e => setForm({...form, name: e.target.value})}
            className="w-full border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"/>
        </div>
        <div>
          <label className="text-sm text-gray-600 block mb-1">Email</label>
          <input required type="email" value={form.email} onChange={e => setForm({...form, email: e.target.value})}
            className="w-full border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"/>
        </div>
        <div>
          <label className="text-sm text-gray-600 block mb-1">Shipping Address</label>
          <textarea required value={form.address} onChange={e => setForm({...form, address: e.target.value})}
            rows={3} className="w-full border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"/>
        </div>
        <button type="submit" className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-3 rounded-lg font-medium">
          Place Order
        </button>
      </form>
    </div>
  )
}
