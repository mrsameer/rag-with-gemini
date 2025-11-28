import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Upload, Trash2, FileText, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';

const DocumentManager = () => {
    const [documents, setDocuments] = useState([]);
    const [uploading, setUploading] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);

    useEffect(() => {
        fetchDocuments();
    }, []);

    const fetchDocuments = async () => {
        try {
            const response = await axios.get('http://localhost:8000/documents');
            setDocuments(response.data);
            setError(null);
        } catch (err) {
            setError('Failed to fetch documents');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setUploading(true);
        setError(null);
        setSuccess(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            await axios.post('http://localhost:8000/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setSuccess('Document uploaded successfully');
            fetchDocuments();
        } catch (err) {
            setError('Failed to upload document');
            console.error(err);
        } finally {
            setUploading(false);
        }
    };

    const handleDelete = async (fileId) => {
        if (!window.confirm('Are you sure you want to delete this document?')) return;

        try {
            await axios.delete(`http://localhost:8000/documents/${fileId}`);
            setSuccess('Document deleted successfully');
            fetchDocuments();
        } catch (err) {
            setError('Failed to delete document');
            console.error(err);
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <div className="bg-slate-900/50 rounded-2xl border border-slate-800 p-8 shadow-xl">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h2 className="text-2xl font-bold text-white mb-2">Document Management</h2>
                        <p className="text-slate-400">Upload and manage your knowledge base documents</p>
                    </div>
                    <div className="relative">
                        <input
                            type="file"
                            onChange={handleFileUpload}
                            className="hidden"
                            id="file-upload"
                            disabled={uploading}
                        />
                        <label
                            htmlFor="file-upload"
                            className={`flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl cursor-pointer transition-all shadow-lg shadow-indigo-500/20 font-medium ${uploading ? 'opacity-50 cursor-not-allowed' : ''
                                }`}
                        >
                            {uploading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Upload className="w-5 h-5" />}
                            {uploading ? 'Uploading...' : 'Upload Document'}
                        </label>
                    </div>
                </div>

                {error && (
                    <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 flex items-center gap-2">
                        <AlertCircle className="w-5 h-5" />
                        {error}
                    </div>
                )}

                {success && (
                    <div className="mb-6 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-400 flex items-center gap-2">
                        <CheckCircle2 className="w-5 h-5" />
                        {success}
                    </div>
                )}

                <div className="space-y-4">
                    {loading ? (
                        <div className="flex justify-center py-12">
                            <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
                        </div>
                    ) : documents.length === 0 ? (
                        <div className="text-center py-12 border-2 border-dashed border-slate-800 rounded-xl bg-slate-900/30">
                            <div className="w-16 h-16 bg-slate-800/50 rounded-full flex items-center justify-center mx-auto mb-4">
                                <FileText className="w-8 h-8 text-slate-500" />
                            </div>
                            <h3 className="text-lg font-medium text-slate-300 mb-1">No documents yet</h3>
                            <p className="text-slate-500">Upload documents to start chatting with them</p>
                        </div>
                    ) : (
                        <div className="grid gap-4">
                            {documents.map((doc) => (
                                <div
                                    key={doc.id}
                                    className="flex items-center justify-between p-4 bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 rounded-xl transition-all group"
                                >
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 bg-indigo-500/10 rounded-lg flex items-center justify-center border border-indigo-500/20">
                                            <FileText className="w-5 h-5 text-indigo-400" />
                                        </div>
                                        <div>
                                            <h3 className="font-medium text-slate-200">{doc.display_name}</h3>
                                            <p className="text-xs text-slate-500 font-mono mt-0.5">{doc.id}</p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => handleDelete(doc.id)}
                                        className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all opacity-0 group-hover:opacity-100"
                                        title="Delete document"
                                    >
                                        <Trash2 className="w-5 h-5" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default DocumentManager;
