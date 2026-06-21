import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../api'

export default function ProductDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [product, setProduct] = useState(null)
  const [qty, setQty] = useState(1)
  const [added, setAdded] = useState(false)
  const sessionId = (() => {
    let s = localStorage.getItem('session_id')
    if (!s) { s = Math.random().toString(36).slice(2)+Date.now().toString(36); localStorage.setItem('session_id', s) }
    return s
  })()

  useEffect(() => {
    api.getProduct(id).then(r => setProduct(r.data)).catch(() => navigate('/'))
  }, [id])

  const addToCart = async () => {
    await api.addToCart(sessionId, { product_id: id, qty })
    setAdded(true)
    setTimeout(() => setAdded(false), 2000)
  }

  if (!product) return (
    <div className="flex justify-center items-center h-64">
      <div className="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full"/>
    </div>
  )

  return (
    <div className="max-w-4xl mx-auto px-4 py-10">
      <button onClick={() => navigate(-1)} className="text-indigo-600 text-sm mb-6 hover:underline">← Back</button>
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 flex flex-col md:flex-row gap-10">
        <div className="flex-shrink-0 w-full md:w-64 flex items-center justify-center bg-gray-50 rounded-xl p-6">
          <img src={product.image_url} alt={product.name} className="max-h-56 object-contain"/>
        </div>
        <div className="flex-1">
          <p className="text-xs text-gray-400 capitalize mb-2">{product.category}</p>
          <h1 className="text-2xl font-bold text-gray-900 mb-4">{product.name}</h1>
          <p className="text-3xl font-bold text-indigo-600 mb-4">£{Number(product.price).toFixed(2)}</p>
          <p className="text-sm text-gray-500 mb-4">⭐ {product.rating_rate} ({product.rating_count} reviews)</p>
          <p className="text-gray-600 text-sm leading-relaxed mb-6">{product.description}</p>
          <div className="flex items-center gap-4">
            <select value={qty} onChange={e => setQty(Number(e.target.value))}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm">
              {[1,2,3,4,5].map(n => <option key={n} value={n}>{n}</option>)}
            </select>
            <button onClick={addToCart}
              className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${added ? 'bg-green-500 text-white' : 'bg-indigo-600 hover:bg-indigo-700 text-white'}`}>
              {added ? '✓ Added to Cart' : 'Add to Cart'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
