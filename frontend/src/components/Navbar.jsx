import { Link } from 'react-router-dom'
import { useEffect, useState } from 'react'
import api from '../api'

export default function Navbar() {
  const [cartCount, setCartCount] = useState(0)
  const sessionId = (() => {
    let s = localStorage.getItem('session_id')
    if (!s) { s = Math.random().toString(36).slice(2)+Date.now().toString(36); localStorage.setItem('session_id', s) }
    return s
  })()
  useEffect(() => {
    api.getCart(sessionId).then(r => setCartCount(r.data.item_count || 0)).catch(() => {})
  }, [])
  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <Link to="/" className="text-xl font-bold text-indigo-600">RetailAI Store</Link>
        <div className="flex items-center gap-6">
          <Link to="/" className="text-gray-600 hover:text-indigo-600 text-sm">Products</Link>
          <Link to="/cart" className="relative text-gray-600 hover:text-indigo-600 text-sm">
            🛒 Cart
            {cartCount > 0 && <span className="ml-1 bg-indigo-600 text-white text-xs rounded-full px-1">{cartCount}</span>}
          </Link>
        </div>
      </div>
    </nav>
  )
}
