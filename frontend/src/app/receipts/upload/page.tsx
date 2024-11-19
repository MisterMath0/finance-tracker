// src/app/receipts/upload/page.tsx
import { ReceiptUploader } from "@/components/receipts/receipt-uploader"

export default function UploadPage() {
  return (
    <main className="container mx-auto p-4 max-w-4xl">
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-center">Upload Receipt</h1>
        <ReceiptUploader />
      </div>
    </main>
  )
}