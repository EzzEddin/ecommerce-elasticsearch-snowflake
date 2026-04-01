import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Star, Package, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { api, Product } from '../api';

export default function ProductDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    api.getProduct(id)
      .then(setProduct)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center">
        <p className="text-gray-500">{error || 'Product not found'}</p>
        <Link to="/" className="text-indigo-600 hover:underline mt-4 inline-block">
          Back to search
        </Link>
      </div>
    );
  }

  const inStock = product.inventory ? product.inventory.available > 0 : false;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Link
        to="/"
        className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900 mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to search
      </Link>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-0">
          {/* Image */}
          <div className="bg-gray-100 aspect-square flex items-center justify-center">
            {product.image_url ? (
              <img
                src={product.image_url}
                alt={product.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <Package className="w-24 h-24 text-gray-300" />
            )}
          </div>

          {/* Details */}
          <div className="p-8">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm text-indigo-600 font-medium">{product.category.name}</span>
              <span className="text-gray-300">|</span>
              <span className="text-sm text-gray-500">{product.brand}</span>
            </div>

            <h1 className="text-2xl font-bold text-gray-900 mb-2">{product.name}</h1>

            <div className="flex items-center gap-3 mb-4">
              <div className="flex items-center gap-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <Star
                    key={star}
                    className={`w-4 h-4 ${
                      star <= Math.round(product.rating)
                        ? 'text-amber-400 fill-amber-400'
                        : 'text-gray-200'
                    }`}
                  />
                ))}
              </div>
              <span className="text-sm text-gray-600">
                {product.rating.toFixed(1)} ({product.review_count} reviews)
              </span>
            </div>

            <div className="text-3xl font-bold text-gray-900 mb-4">
              ${product.price.toFixed(2)}
            </div>

            {product.description && (
              <p className="text-gray-600 text-sm leading-relaxed mb-6">
                {product.description}
              </p>
            )}

            {/* Stock Status */}
            <div className="flex items-center gap-2 mb-6">
              {inStock ? (
                <>
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <span className="text-green-700 font-medium text-sm">
                    In Stock ({product.inventory?.available} available)
                  </span>
                </>
              ) : (
                <>
                  <XCircle className="w-5 h-5 text-red-500" />
                  <span className="text-red-700 font-medium text-sm">Out of Stock</span>
                </>
              )}
            </div>

            {/* Product Details Table */}
            <div className="border-t border-gray-200 pt-4">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Product Details</h3>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-gray-500">SKU</dt>
                  <dd className="text-gray-900 font-mono">{product.sku}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Brand</dt>
                  <dd className="text-gray-900">{product.brand}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Category</dt>
                  <dd className="text-gray-900">{product.category.name}</dd>
                </div>
                {product.inventory && (
                  <>
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Total Stock</dt>
                      <dd className="text-gray-900">{product.inventory.quantity}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Reserved</dt>
                      <dd className="text-gray-900">{product.inventory.reserved}</dd>
                    </div>
                  </>
                )}
              </dl>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
