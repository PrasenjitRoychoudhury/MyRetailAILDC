import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'

export default function ProductListPage() {
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [selectedCat, setSelectedCat] = useState(null)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get('/v1/categories').then(r => setCategories(r.data.categories)).catch(() => {})
  }, [])

  useEffect(() => {
    setLoading(true)
    const url = search
      ? `/v1/search?q=${encodeURIComponent(search)}${selectedCat ? `&category=${selectedCat}` : ''}`
      : `/v1/products${selectedCat ? `?category=${selectedCat}` : ''}`
    axios.get(url).then(r => {
      setProducts(r.data.products || r.data.results || [])
    }).finally(() => setLoading(false))
  }, [selectedCat, search])

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        <input
          className="border border-gray-300 rounded-lg px-4 py-2 flex-1 focus:outline-none focus:ring-2 focus:ring-indigo-400"
          placeholder="Search products..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>
      <div className="flex gap-2 flex-wrap mb-6">
        <button onClick={() => setSelectedCat(null)}
          className={`px-4 py-1 rounded-full text-sm border ${!selectedCat ? 'bg-indigo-600 text-white border-indigo-600' : 'border-gray-300 text-gray-600 hover:border-indigo-400'}`}>
          All
        </button>
        {categories.map(c => (
          <button key={c.slug} onClick={() => setSelectedCat(c.slug)}
            className={`px-4 py-1 rounded-full text-sm border capitalize ${selectedCat === c.slug ? 'bg-indigo-600 text-white border-indigo-600' : 'border-gray-300 text-gray-600 hover:border-indigo-400'}`}>
            {c.display_name}
          </button>
        ))}
      </div>
      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-6">
          {[...Array(8)].map((_, i) => <div key={i} className="bg-gray-200 animate-pulse rounded-xl h-64"/>)}
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-6">
          {products.map(p => (
            <Link key={p.product_id} to={`/products/${p.product_id}`}
              className="bg-white rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow overflow-hidden">
              <div className="h-48 flex items-center justify-center p-4 bg-gray-50">
                <img src={p.image_url} alt={p.name} className="max-h-full max-w-full object-contain"/>
              </div>
              <div className="p-4">
                <p className="text-sm text-gray-800 font-medium line-clamp-2 mb-2">{p.name}</p>
                <p className="text-indigo-600 font-bold">£{Number(p.price).toFixed(2)}</p>
                <p className="text-xs text-gray-400 capitalize mt-1">{p.category}</p>
              </div>
            </Link>
          ))}
        </div>
      )}
      {!loading && products.length === 0 && (
        <div className="text-center py-16 text-gray-400">No products found.</div>
      )}
    </div>
  )
}
