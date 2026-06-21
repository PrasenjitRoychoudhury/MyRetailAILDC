import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../api'

export default function CartPage() {
  const [cart, setCart] = useState(null)
  const navigate = useNavigate()
  const sessionId = (() => {
    let s = localStorage.getItem('session_id')
    if (!s) { s = Math.random().toString(36).slice(2)+Date.now().toString(36); localStorage.setItem('session_id', s) }
    return s
  })()

  const fetchCart = () => api.getCart(sessionId)
    .then(r => setCart(r.data))
    .catch(() => setCart({ items: [], subtotal: 0, item_count: 0 }))

  useEffect(() => { fetchCart() }, [])

  const updateQty = (pid, qty) => api.updateCart(sessionId, pid, { qty }).then(fetchCart)
  const removeItem = (pid) => api.removeFromCart(sessionId, pid).then(fetchCart)

  if (!cart) return <div className="flex justify-center items-center h-64"><div className="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full"/></div>

  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <h1 className="text-2xl font-bold text-gray-900 mb-8">Shopping Cart</h1>
      {cart.items.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-gray-400 mb-4">Your cart is empty.</p>
          <Link to="/" className="text-indigo-600 hover:underline text-sm">Continue shopping</Link>
        </div>
      ) : (
        <>
          <div className="space-y-4 mb-8">
            {cart.items.map(item => (
              <div key={item.product_id} className="bg-white rounded-xl border border-gray-100 p-4 flex items-center gap-4">
                {item.image_url && <img src={item.image_url} alt={item.name} className="w-16 h-16 object-contain bg-gray-50 rounded-lg"/>}
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-800">{item.name}</p>
                  <p className="text-indigo-600 font-bold mt-1">£{Number(item.unit_price).toFixed(2)}</p>
                </div>
                <select value={item.qty} onChange={e => updateQty(item.product_id, Number(e.target.value))}
                  className="border border-gray-300 rounded-lg px-2 py-1 text-sm">
                  {[1,2,3,4,5].map(n => <option key={n} value={n}>{n}</option>)}
                </select>
                <button onClick={() => removeItem(item.product_id)} className="text-red-400 hover:text-red-600 text-sm">Remove</button>
              </div>
            ))}
          </div>
          <div className="bg-white rounded-xl border border-gray-100 p-6">
            <div className="flex justify-between text-lg font-bold mb-4">
              <span>Subtotal</span>
              <span className="text-indigo-600">£{Number(cart.subtotal).toFixed(2)}</span>
            </div>
            <button onClick={() => navigate('/checkout')}
              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-3 rounded-lg font-medium">
              Proceed to Checkout
            </button>
          </div>
        </>
      )}
    </div>
  )
}
