import { useRef } from 'react'
import { Link } from 'react-router-dom'
import { motion, useScroll, useTransform } from 'framer-motion'
import {
  Zap,
  Network,
  Shield,
  TrendingUp,
  Code,
  Globe,
  ArrowRight,
  Github,
  Play,
  ChevronDown,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import NetworkAnimation from '@/components/three/NetworkAnimation'

const features = [
  {
    icon: Network,
    title: 'Topology Analysis',
    description: 'Deep analysis of your microservice dependency graph using advanced network metrics.',
    color: 'from-edge-500 to-edge-600',
  },
  {
    icon: Zap,
    title: 'Smart Shortcuts',
    description: 'AI-powered suggestions for optimal shortcut edges that reduce latency and improve resilience.',
    color: 'from-neural-500 to-neural-600',
  },
  {
    icon: Shield,
    title: 'Self-Healing',
    description: 'Predictive alerts and automated recommendations before failures occur.',
    color: 'from-success-500 to-success-600',
  },
  {
    icon: TrendingUp,
    title: 'Performance Boost',
    description: 'Reduce average path length by up to 50% with intelligent topology optimization.',
    color: 'from-warning-500 to-warning-600',
  },
]

const stats = [
  { value: '50%', label: 'Latency Reduction' },
  { value: '3x', label: 'Resilience Boost' },
  { value: '10K+', label: 'Services Analyzed' },
  { value: '99.9%', label: 'Uptime' },
]

export default function LandingPage() {
  const heroRef = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ['start start', 'end start'],
  })

  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0])
  const scale = useTransform(scrollYProgress, [0, 0.5], [1, 0.95])
  const y = useTransform(scrollYProgress, [0, 0.5], [0, 100])

  return (
    <div className="min-h-screen bg-slate-950 overflow-x-hidden">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-slate-950/80 backdrop-blur-xl border-b border-slate-800/50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="relative">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-edge-500 to-neural-500 flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-edge-500 to-neural-500 blur-lg opacity-50 group-hover:opacity-75 transition-opacity" />
            </div>
            <span className="font-display font-bold text-xl gradient-text">EdgeWise</span>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-slate-400 hover:text-white transition-colors">Features</a>
            <a href="#demo" className="text-slate-400 hover:text-white transition-colors">Demo</a>
            <a href="#about" className="text-slate-400 hover:text-white transition-colors">About</a>
            <a href="https://github.com/edgewise/edgewise" target="_blank" rel="noopener" className="text-slate-400 hover:text-white transition-colors">
              <Github className="w-5 h-5" />
            </a>
          </div>

          <div className="flex items-center gap-4">
            <Link to="/dashboard" className="btn-glow">
              Launch App
              <ArrowRight className="w-4 h-4 ml-2 inline-block" />
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section ref={heroRef} className="relative min-h-screen pt-16 overflow-hidden">
        {/* Background effects */}
        <div className="absolute inset-0 grid-bg opacity-30" />
        <div className="absolute top-1/4 left-1/4 w-[600px] h-[600px] bg-edge-500/20 rounded-full blur-[128px]" />
        <div className="absolute bottom-1/4 right-1/4 w-[600px] h-[600px] bg-neural-500/20 rounded-full blur-[128px]" />

        {/* 3D Network Animation - disabled for compatibility */}
        {/* <div className="absolute inset-0 opacity-60">
          <NetworkAnimation />
        </div> */}

        <motion.div
          style={{ opacity, scale, y }}
          className="relative z-10 max-w-7xl mx-auto px-6 pt-32 pb-20 text-center"
        >
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="inline-flex items-center gap-2 px-4 py-2 bg-edge-500/10 border border-edge-500/30 rounded-full text-edge-400 text-sm font-medium mb-8"
          >
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-edge-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-edge-500" />
            </span>
            Now with Predictive Self-Healing
          </motion.div>

          {/* Title */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="text-5xl md:text-7xl font-display font-bold leading-tight mb-6"
          >
            Intelligent Topology
            <br />
            <span className="gradient-text">Optimization</span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="text-xl text-slate-400 max-w-2xl mx-auto mb-12"
          >
            EdgeWise enables distributed systems to think, adapt, and self-heal in real-time.
            Explore the future of resilient microservice networks.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16"
          >
            <Link to="/dashboard" className="btn-glow px-8 py-4 text-lg">
              Get Started Free
              <ArrowRight className="w-5 h-5 ml-2 inline-block" />
            </Link>
            <button className="px-8 py-4 text-lg font-semibold text-white border border-slate-700 rounded-xl hover:bg-slate-800/50 transition-colors flex items-center gap-2">
              <Play className="w-5 h-5" />
              Watch Demo
            </button>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-3xl mx-auto"
          >
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl md:text-4xl font-display font-bold gradient-text mb-1">
                  {stat.value}
                </div>
                <div className="text-sm text-slate-500">{stat.label}</div>
              </div>
            ))}
          </motion.div>

          {/* Scroll indicator */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1 }}
            className="absolute bottom-8 left-1/2 -translate-x-1/2"
          >
            <ChevronDown className="w-6 h-6 text-slate-500 animate-bounce" />
          </motion.div>
        </motion.div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-32 relative">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-display font-bold mb-6">
              Powerful <span className="gradient-text">Features</span>
            </h2>
            <p className="text-xl text-slate-400 max-w-2xl mx-auto">
              Everything you need to optimize your microservice topology and build resilient distributed systems.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="glass-card p-8 group hover:border-edge-500/30 transition-colors"
              >
                <div
                  className={cn(
                    'w-14 h-14 rounded-2xl bg-gradient-to-br flex items-center justify-center mb-6',
                    feature.color
                  )}
                >
                  <feature.icon className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-2xl font-semibold text-white mb-3">{feature.title}</h3>
                <p className="text-slate-400 leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Demo Section */}
      <section id="demo" className="py-32 relative bg-gradient-to-b from-transparent via-slate-900/50 to-transparent">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-display font-bold mb-6">
              See it in <span className="gradient-text">Action</span>
            </h2>
            <p className="text-xl text-slate-400 max-w-2xl mx-auto">
              Watch how EdgeWise transforms a chaotic microservice graph into an optimized small-world network.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="glass-card overflow-hidden"
          >
            <div className="aspect-video bg-slate-900 flex items-center justify-center">
              <div className="text-center">
                <div className="w-20 h-20 rounded-full bg-edge-500/20 flex items-center justify-center mx-auto mb-4 cursor-pointer hover:bg-edge-500/30 transition-colors">
                  <Play className="w-10 h-10 text-edge-400 ml-1" />
                </div>
                <p className="text-slate-400">Interactive Demo Coming Soon</p>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-32 relative">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="glass-card p-12 relative overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-edge-500/10 via-neural-500/10 to-edge-500/10" />
            <div className="relative z-10">
              <h2 className="text-3xl md:text-4xl font-display font-bold mb-6">
                Ready to Optimize Your Architecture?
              </h2>
              <p className="text-xl text-slate-400 mb-8 max-w-2xl mx-auto">
                Join thousands of engineers using EdgeWise to build more resilient distributed systems.
              </p>
              <Link to="/dashboard" className="btn-glow px-10 py-4 text-lg inline-flex items-center">
                Start Free Trial
                <ArrowRight className="w-5 h-5 ml-2" />
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-slate-800/50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-edge-500 to-neural-500 flex items-center justify-center">
                <Zap className="w-4 h-4 text-white" />
              </div>
              <span className="font-display font-bold gradient-text">EdgeWise</span>
            </div>

            <div className="flex items-center gap-6 text-sm text-slate-500">
              <a href="#" className="hover:text-white transition-colors">Documentation</a>
              <a href="#" className="hover:text-white transition-colors">API Reference</a>
              <a href="#" className="hover:text-white transition-colors">Support</a>
              <a href="#" className="hover:text-white transition-colors">Privacy</a>
            </div>

            <div className="flex items-center gap-4">
              <a href="https://github.com/edgewise" target="_blank" rel="noopener" className="text-slate-400 hover:text-white transition-colors">
                <Github className="w-5 h-5" />
              </a>
              <Globe className="w-5 h-5 text-slate-400" />
            </div>
          </div>

          <div className="mt-8 pt-8 border-t border-slate-800/50 text-center text-sm text-slate-500">
            © 2024 EdgeWise. Built with Small-World Network Theory.
          </div>
        </div>
      </footer>
    </div>
  )
}
