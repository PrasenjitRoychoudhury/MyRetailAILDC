import { Link } from 'react-router-dom'
import { useEffect, useState } from 'react'
import axios from 'axios'

export default function Navbar() {
  const [cartCount, setCartCount] = useState(0)
  const sessionId = (() => {
    let id = localStorage.getItem('session_id')
    if (!id) { id = crypto.randomUUID(); localStorage.setItem('session_id', id) }
    return id
  })()
  useEffect(() => {
    axios.get(`/v1/cart/${sessionId}`).then(r => setCartCount(r.data.item_count)).catch(() => {})
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
