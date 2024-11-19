// src/components/receipts/receipt-uploader.tsx
"use client"

import { useState } from "react"
import { Upload, Loader2 } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"

interface ReceiptItem {
  description: string
  quantity: number
  price: number
  category: string
}

interface Receipt {
  id?: number
  store_name: string
  date: string
  items: ReceiptItem[]
  subtotal: number
  tax: number
  total: number
  categories_summary: {
    [key: string]: {
      count: number
      total: number
    }
  }
}

export function ReceiptUploader() {
  const [uploading, setUploading] = useState(false)
  const [receipt, setReceipt] = useState<Receipt | null>(null)
  const [error, setError] = useState("")

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      setUploading(true)
      setError("")

      const formData = new FormData()
      formData.append("file", file)

      const response = await fetch("http://localhost:8000/api/receipts/upload", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        throw new Error("Failed to upload receipt")
      }

      const data = await response.json()
      setReceipt(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload receipt")
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-8">
      <Card>
        <CardHeader>
          <CardTitle>Upload Receipt</CardTitle>
        </CardHeader>
        <CardContent>
          <Label htmlFor="receipt-upload" className="w-full">
            <div className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 hover:border-muted-foreground/50 transition-colors cursor-pointer">
              <input
                id="receipt-upload"
                type="file"
                accept="image/*"
                onChange={handleUpload}
                className="hidden"
              />
              <div className="flex flex-col items-center gap-2">
                {uploading ? (
                  <>
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">
                      Processing receipt...
                    </p>
                  </>
                ) : (
                  <>
                    <Upload className="h-8 w-8 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">
                      Click to upload receipt image
                    </p>
                  </>
                )}
              </div>
            </div>
          </Label>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {receipt && (
        <Card>
          <CardHeader>
            <CardTitle>{receipt.store_name}</CardTitle>
            <p className="text-sm text-muted-foreground">
              {new Date(receipt.date).toLocaleDateString()}
            </p>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Items Table */}
            <div className="relative overflow-x-auto rounded-lg border">
              <table className="w-full text-sm">
                <thead className="text-xs uppercase bg-muted">
                  <tr>
                    <th scope="col" className="px-4 py-2 text-left">
                      Item
                    </th>
                    <th scope="col" className="px-4 py-2 text-right">
                      Qty
                    </th>
                    <th scope="col" className="px-4 py-2 text-right">
                      Price
                    </th>
                    <th scope="col" className="px-4 py-2 text-right">
                      Total
                    </th>
                    <th scope="col" className="px-4 py-2 text-left">
                      Category
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {receipt.items.map((item, index) => (
                    <tr key={index}>
                      <td className="px-4 py-2">{item.description}</td>
                      <td className="px-4 py-2 text-right">{item.quantity}</td>
                      <td className="px-4 py-2 text-right">
                        ${item.price.toFixed(2)}
                      </td>
                      <td className="px-4 py-2 text-right">
                        ${(item.quantity * item.price).toFixed(2)}
                      </td>
                      <td className="px-4 py-2">{item.category}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Categories Summary */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {Object.entries(receipt.categories_summary).map(([category, data]) => (
                <Card key={category}>
                  <CardHeader>
                    <CardTitle className="text-sm">
                      {category.replace("_", " ").toUpperCase()}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      ${data.total.toFixed(2)}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {data.count} items
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Totals */}
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Subtotal</span>
                <span>${receipt.subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Tax</span>
                <span>${receipt.tax.toFixed(2)}</span>
              </div>
              <div className="flex justify-between border-t pt-2">
                <span className="font-medium">Total</span>
                <span className="font-bold">${receipt.total.toFixed(2)}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}