import React, { useState } from 'react';
import axios from 'axios';
import { Search, Sparkles, TrendingUp, ArrowRight, Video, User, Clock, ChevronLeft } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import Slider from 'rc-slider';
import 'rc-slider/assets/index.css';

const App = () => {
    const [niche, setNiche] = useState('');
    const [loading, setLoading] = useState(false);
    const [step, setStep] = useState(1); // 1: Niche, 2: Keywords, 3: Analysis
    const [keywords, setKeywords] = useState([]);
    const [selectedKeyword, setSelectedKeyword] = useState('');
    const [videos, setVideos] = useState([]);
    const [timeFilter, setTimeFilter] = useState('7_days');
    const [videoType, setVideoType] = useState('any'); // any, shorts, normal
    const [smallChannels, setSmallChannels] = useState(false);
    const [viewRange, setViewRange] = useState([0, 100]); // 0-100 linear value

    // Logarithmic Scale Helpers
    const minView = 1000;
    const maxView = 10000000;
    const minLog = Math.log(minView);
    const maxLog = Math.log(maxView);
    const scale = (maxLog - minLog) / 100;

    const toLog = (val) => Math.round(Math.exp(minLog + scale * val));
    const toLinear = (val) => Math.round((Math.log(val) - minLog) / scale);

    const formatViewCount = (val) => {
        if (val >= 1000000) return (val / 1000000).toFixed(1) + 'M';
        if (val >= 1000) return (val / 1000).toFixed(0) + 'k';
        return val;
    };

    // Re-run analysis when time filter or video type changes
    React.useEffect(() => {
        if (selectedKeyword && step === 3) {
            handleSelectKeyword(selectedKeyword, timeFilter, videoType, smallChannels, viewRange);
        }
    }, [timeFilter, videoType, smallChannels]); // viewRange is manual apply only

    const handleDiscover = async () => {
        if (!niche) return;
        setLoading(true);
        try {
            const response = await axios.post('/api/discover', { niche });
            setKeywords(response.data.keywords);
            setStep(2);
        } catch (error) {
            console.error("Error discovering keywords:", error);
            alert("Error al descubrir keywords. ¿Está el backend encendido?");
        } finally {
            setLoading(false);
        }
    };


    const handleGenerateViralIdeas = async () => {
        setLoading(true);
        try {
            const response = await axios.post('/api/generate-viral-ideas');
            setKeywords(response.data.keywords);
            setNiche("Ideas Virales Aleatorias");
            setStep(2);
        } catch (error) {
            console.error("Error generating viral ideas:", error);
            alert("Error al generar ideas virales.");
        } finally {
            setLoading(false);
        }
    };

    const handleSelectKeyword = async (kw, filter = timeFilter, type = videoType, small = smallChannels, range = viewRange) => {
        setSelectedKeyword(kw);
        setLoading(true);
        try {
            const minV = toLog(range[0]);
            const maxV = toLog(range[1]);

            const response = await axios.post('/api/analyze', {
                keyword: kw,
                time_filter: filter,
                video_type: type,
                small_channels_only: small,
                min_view_count: minV,
                max_view_count: maxV
            });
            setVideos(response.data.videos);
            setStep(3);
        } catch (error) {
            console.error("Error analyzing videos:", error);
            alert("Error al analizar videos.");
        } finally {
            setLoading(false);
        }
    };

    const getTrendClass = (trend) => {
        if (trend === 'alta') return 'trend-high';
        if (trend === 'media') return 'trend-medium';
        return 'trend-emerging';
    };

    const filters = (
        <div style={{ marginBottom: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div>
                <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>Rango de tiempo:</p>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {[
                        { label: 'Últimas horas', val: 'hours' },
                        { label: '3 Días', val: '3_days' },
                        { label: '7 Días', val: '7_days' },
                        { label: '1 Mes', val: 'month' },
                        { label: '3 Meses', val: '3_months' },
                        { label: '7 Meses', val: '7_months' }
                    ].map((f) => (
                        <button
                            key={f.val}
                            onClick={() => setTimeFilter(f.val)}
                            className="filter-btn"
                            disabled={loading}
                            style={{
                                background: timeFilter === f.val ? 'var(--primary)' : 'var(--glass-bg)',
                                padding: '0.5rem 1rem',
                                fontSize: '0.9rem',
                                borderRadius: '12px',
                                border: '1px solid rgba(255,255,255,0.1)',
                                cursor: loading ? 'not-allowed' : 'pointer',
                                transition: 'all 0.3s ease'
                            }}
                        >
                            {f.label}
                        </button>
                    ))}
                </div>
            </div>

            <div>
                <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>Formato de Video:</p>
                <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                        {[
                            { label: 'Cualquiera', val: 'any' },
                            { label: 'Shorts (< 4m)', val: 'shorts' },
                            { label: 'Normal (> 4m)', val: 'normal' }
                        ].map((v) => (
                            <button
                                key={v.val}
                                onClick={() => setVideoType(v.val)}
                                className="filter-btn"
                                disabled={loading}
                                style={{
                                    background: videoType === v.val ? 'var(--secondary)' : 'var(--glass-bg)',
                                    padding: '0.5rem 1rem',
                                    fontSize: '0.9rem',
                                    borderRadius: '12px',
                                    border: '1px solid rgba(255,255,255,0.1)',
                                    cursor: loading ? 'not-allowed' : 'pointer',
                                    paddingLeft: '1.5rem',
                                    paddingRight: '1.5rem',
                                    transition: 'all 0.3s ease'
                                }}
                            >
                                {v.label}
                            </button>
                        ))}
                    </div>

                    <button
                        onClick={() => setSmallChannels(!smallChannels)}
                        className="filter-btn"
                        disabled={loading}
                        style={{
                            background: smallChannels ? '#10b981' : 'var(--glass-bg)',
                            padding: '0.5rem 1rem',
                            fontSize: '0.9rem',
                            borderRadius: '12px',
                            border: smallChannels ? '1px solid #10b981' : '1px solid rgba(255,255,255,0.1)',
                            cursor: loading ? 'not-allowed' : 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            color: 'white',
                            transition: 'all 0.3s ease'
                        }}
                    >
                        <User size={16} />
                        {smallChannels ? 'Solo Canales Pequeños (<1M) [ACTIVO]' : 'Filtrar Canales Grandes'}
                    </button>
                </div>
            </div>

            <div style={{ width: '100%', marginTop: '0rem' }}>
                <p style={{ color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                    Filtrar por Visitas: <span style={{ color: 'var(--primary)', fontWeight: 'bold' }}>{formatViewCount(toLog(viewRange[0]))} - {formatViewCount(toLog(viewRange[1]))}</span>
                </p>
                <div style={{ padding: '0 10px' }}>
                    <Slider
                        range
                        min={0}
                        max={100}
                        defaultValue={[0, 100]}
                        value={viewRange}
                        onChange={(val) => setViewRange(val)}
                        onAfterChange={() => handleSelectKeyword(selectedKeyword, timeFilter, videoType, smallChannels, viewRange)}
                        trackStyle={[{ backgroundColor: 'var(--primary)', height: 6 }]}
                        railStyle={{ backgroundColor: 'rgba(255,255,255,0.1)', height: 6 }}
                        handleStyle={[
                            {
                                borderColor: 'var(--primary)',
                                height: 20,
                                width: 20,
                                backgroundColor: '#fff',
                                opacity: 1
                            },
                            {
                                borderColor: 'var(--primary)',
                                height: 20,
                                width: 20,
                                backgroundColor: '#fff',
                                opacity: 1
                            }
                        ]}
                    />
                </div>
            </div>
        </div>
    );

    return (
        <div className="app-container">
            <div className="bg-glow glow-1"></div>
            <div className="bg-glow glow-2"></div>

            <header style={{ marginBottom: '4rem' }}>
                <motion.h1
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8 }}
                >
                    TrendsAI
                </motion.h1>
                <motion.h2
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3, duration: 0.8 }}
                >
                    Motor Inteligente de Tendencias para YouTube
                </motion.h2>
            </header>

            <AnimatePresence mode="wait">
                {step === 1 && (
                    <motion.div
                        key="step1"
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        className="card"
                        style={{ maxWidth: '800px', margin: '0 auto' }}
                    >
                        <div style={{ marginBottom: '2rem' }}>
                            <h3 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Define tu nicho o idea</h3>
                            <p style={{ color: 'var(--text-muted)' }}>Describe lo que haces o lo que quieres explorar. Nuestra IA expandirá tu nicho en oportunidades estratégicas.</p>
                        </div>

                        <div className="input-group">
                            <input
                                type="text"
                                placeholder="Ej: Fitness para programadores con poco tiempo..."
                                value={niche}
                                onChange={(e) => setNiche(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && handleDiscover()}
                            />
                            <button onClick={handleDiscover} disabled={loading || !niche}>
                                {loading ? 'Analizando...' : (
                                    <>
                                        Descubrir <Sparkles size={20} />
                                    </>
                                )}
                            </button>
                        </div>

                        <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'center' }}>
                            <button
                                onClick={handleGenerateViralIdeas}
                                disabled={loading}
                                style={{
                                    background: 'var(--glass-bg)',
                                    border: '1px solid var(--primary)',
                                    color: 'white',
                                    padding: '0.8rem 1.5rem',
                                    borderRadius: '12px',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem',
                                    transition: 'all 0.3s ease'
                                }}
                                onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255, 0, 128, 0.2)'}
                                onMouseOut={(e) => e.currentTarget.style.background = 'var(--glass-bg)'}
                            >
                                <Sparkles size={18} color="#ff0080" />
                                {loading ? 'Generando...' : 'Obtener 7 Ideas Virales Aleatorias (Google AI)'}
                            </button>
                        </div>
                    </motion.div>
                )}

                {step === 2 && (
                    <motion.div
                        key="step2"
                        initial={{ opacity: 0, x: 50 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -50 }}
                    >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
                            <button
                                onClick={() => setStep(1)}
                                style={{ background: 'var(--glass-bg)', padding: '0.5rem 1rem' }}
                            >
                                <ChevronLeft size={20} /> Volver
                            </button>
                            <h3 style={{ fontSize: '1.8rem' }}>Resultados para "{niche}"</h3>
                        </div>

                        {filters}

                        <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>Selecciona un ángulo para profundizar en el análisis de videos reales.</p>

                        <div className="keyword-grid">
                            {keywords.map((kw, i) => (
                                <motion.div
                                    key={i}
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                    className="card keyword-card"
                                    onClick={() => handleSelectKeyword(kw)}
                                >
                                    <TrendingUp style={{ color: 'var(--primary)', marginBottom: '1rem' }} />
                                    <h3>{kw}</h3>
                                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '1rem' }}>
                                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Clic para analizar videos</span>
                                        <ArrowRight size={18} />
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                        {loading && (
                            <div style={{ textAlign: 'center', marginTop: '3rem' }}>
                                <p>Analizando competencia y crecimiento en tiempo real...</p>
                            </div>
                        )}
                    </motion.div>
                )}

                {step === 3 && (
                    <motion.div
                        key="step3"
                        initial={{ opacity: 0, y: 30 }}
                        animate={{ opacity: 1, y: 0 }}
                    >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '3rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                <button
                                    onClick={() => setStep(2)}
                                    style={{ background: 'var(--glass-bg)', padding: '0.5rem 1rem' }}
                                >
                                    <ChevronLeft size={20} /> Volver a Keywords
                                </button>
                                <h3 style={{ fontSize: '1.8rem' }}>Análisis: {selectedKeyword}</h3>
                            </div>
                        </div>

                        {filters}

                        <div className="video-grid">
                            {videos.map((video, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: i * 0.1 }}
                                    className="card video-card"
                                    style={{
                                        border: video.is_viral_gem ? '2px solid #ec4899' : '1px solid rgba(255,255,255,0.1)',
                                        background: video.is_viral_gem ? 'rgba(236, 72, 153, 0.1)' : 'var(--glass-bg)'
                                    }}
                                >
                                    <div style={{ position: 'relative' }}>
                                        <img src={video.thumbnail} alt={video.title} className="video-thumbnail" />
                                        {video.is_viral_gem && (
                                            <div style={{
                                                position: 'absolute',
                                                top: '10px',
                                                right: '10px',
                                                background: '#ec4899',
                                                color: 'white',
                                                padding: '4px 8px',
                                                borderRadius: '8px',
                                                fontSize: '0.75rem',
                                                fontWeight: 'bold',
                                                boxShadow: '0 4px 6px rgba(0,0,0,0.3)'
                                            }}>
                                                💎 JOYA VIRAL
                                            </div>
                                        )}
                                    </div>

                                    <div className="video-info">
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                            <span className={`trend-badge ${getTrendClass(video.estimated_trend)}`}>
                                                {video.estimated_trend}
                                            </span>
                                            {video.viral_score > 0 && (
                                                <span style={{
                                                    background: video.viral_score > 1 ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255, 255, 255, 0.1)',
                                                    color: video.viral_score > 1 ? '#34d399' : 'var(--text-muted)',
                                                    padding: '2px 8px',
                                                    borderRadius: '6px',
                                                    fontSize: '0.8rem',
                                                    fontWeight: '600'
                                                }}>
                                                    Score: {video.viral_score}x
                                                </span>
                                            )}
                                        </div>
                                        <a href={video.video_url} target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'none', color: 'inherit' }}>
                                            <h4 style={{
                                                fontSize: '1.1rem',
                                                marginBottom: '1rem',
                                                height: '3rem',
                                                overflow: 'hidden',
                                                display: '-webkit-box',
                                                WebkitLineClamp: 2,
                                                WebkitBoxOrient: 'vertical',
                                                transition: 'color 0.3s ease'
                                            }}
                                                onMouseEnter={(e) => e.target.style.color = 'var(--primary)'}
                                                onMouseLeave={(e) => e.target.style.color = 'inherit'}
                                            >
                                                {video.title}
                                            </h4>
                                        </a>

                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '0.5rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                                <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><User size={14} /> {video.channel}</span>
                                                <span>{video.subscriber_count > 1000000 ? (video.subscriber_count / 1000000).toFixed(1) + 'M' : (video.subscriber_count / 1000).toFixed(1) + 'k'} subs</span>
                                            </div>
                                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                                <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><TrendingUp size={14} /> {parseInt(video.view_count).toLocaleString()} vistas</span>
                                                <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><Clock size={14} /> {video.published_days_ago}d</span>
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {loading && (step === 1 || step === 3) && (
                <div style={{
                    position: 'fixed',
                    top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.4)',
                    backdropFilter: 'blur(4px)',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 100
                }}>
                    <motion.div
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className="card"
                        style={{ padding: '3rem', textAlign: 'center' }}
                    >
                        <Sparkles className="spin" size={48} style={{ color: 'var(--primary)', marginBottom: '1.5rem' }} />
                        <h3>{step === 1 ? 'Orquestando APIs...' : 'Actualizando Tendencias...'}</h3>
                        <p style={{ color: 'var(--text-muted)', marginTop: '0.5rem' }}>Analizando videos reales en el nuevo rango...</p>
                    </motion.div>
                </div>
            )}
        </div>
    );
};

export default App;
