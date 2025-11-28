import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, Bot, User, Loader2, Sparkles, Search } from 'lucide-react';

const ChatInterface = () => {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: 'Hello! I can help you answer questions based on your documents. What would you like to know?' }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMessage = input;
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
        setIsLoading(true);

        try {
            const response = await axios.post('http://localhost:8000/chat', { query: userMessage });
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: response.data.response,
                citations: response.data.citations
            }]);
        } catch (error) {
            console.error('Error sending message:', error);
            setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error while processing your request.' }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-12rem)] bg-slate-900/50 rounded-2xl border border-slate-800 overflow-hidden shadow-2xl">
            <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
                {messages.map((msg, index) => (
                    <div
                        key={index}
                        className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                        {msg.role === 'assistant' && (
                            <div className="w-8 h-8 rounded-full bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20 flex-shrink-0">
                                <Bot className="w-5 h-5 text-indigo-400" />
                            </div>
                        )}

                        <div
                            className={`max-w-[80%] rounded-2xl p-4 shadow-sm ${msg.role === 'user'
                                    ? 'bg-indigo-600 text-white rounded-tr-sm'
                                    : 'bg-slate-800/80 text-slate-200 rounded-tl-sm border border-slate-700/50'
                                }`}
                        >
                            <p className="leading-relaxed whitespace-pre-wrap">{msg.content}</p>

                            {msg.citations && msg.citations.length > 0 && (
                                <div className="mt-3 pt-3 border-t border-slate-700/50">
                                    <p className="text-xs font-semibold text-slate-400 mb-2 flex items-center gap-1">
                                        <Search className="w-3 h-3" />
                                        Sources
                                    </p>
                                    <div className="flex flex-wrap gap-2">
                                        {msg.citations.map((citation, idx) => (
                                            <span key={idx} className="text-xs bg-slate-900/50 px-2 py-1 rounded border border-slate-700/50 text-slate-400">
                                                {citation}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {msg.role === 'user' && (
                            <div className="w-8 h-8 rounded-full bg-slate-700/50 flex items-center justify-center border border-slate-600/50 flex-shrink-0">
                                <User className="w-5 h-5 text-slate-300" />
                            </div>
                        )}
                    </div>
                ))}
                {isLoading && (
                    <div className="flex gap-4">
                        <div className="w-8 h-8 rounded-full bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20">
                            <Sparkles className="w-5 h-5 text-indigo-400 animate-pulse" />
                        </div>
                        <div className="bg-slate-800/80 rounded-2xl rounded-tl-sm p-4 border border-slate-700/50 flex items-center gap-2">
                            <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
                            <span className="text-sm text-slate-400">Thinking...</span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="p-4 bg-slate-900/80 border-t border-slate-800 backdrop-blur-sm">
                <form onSubmit={handleSubmit} className="relative max-w-4xl mx-auto">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask a question about your documents..."
                        className="w-full bg-slate-800/50 text-slate-200 placeholder-slate-500 rounded-xl pl-4 pr-12 py-3.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:bg-slate-800 transition-all border border-slate-700/50"
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        disabled={isLoading || !input.trim()}
                        className="absolute right-2 top-2 p-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-indigo-500/20"
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </form>
            </div>
        </div>
    );
};

export default ChatInterface;
