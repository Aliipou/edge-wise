import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Trophy,
  Medal,
  Star,
  TrendingUp,
  Zap,
  Target,
  Award,
  Crown,
  ChevronRight,
  Calendar,
  Filter,
} from 'lucide-react'
import { useStore } from '@/store/useStore'
import { cn } from '@/lib/utils'

interface LeaderboardEntry {
  rank: number
  userId: string
  username: string
  avatar: string
  score: number
  optimizations: number
  streak: number
  achievements: string[]
  trend: 'up' | 'down' | 'same'
  trendAmount: number
}

interface Achievement {
  id: string
  name: string
  description: string
  icon: string
  rarity: 'common' | 'rare' | 'epic' | 'legendary'
  unlockedAt?: string
  progress?: number
  maxProgress?: number
}

const mockLeaderboard: LeaderboardEntry[] = [
  {
    rank: 1,
    userId: '1',
    username: 'topology_master',
    avatar: 'TM',
    score: 15420,
    optimizations: 87,
    streak: 14,
    achievements: ['first_optimization', 'streak_7', 'top_10'],
    trend: 'same',
    trendAmount: 0,
  },
  {
    rank: 2,
    userId: '2',
    username: 'graph_wizard',
    avatar: 'GW',
    score: 12350,
    optimizations: 65,
    streak: 8,
    achievements: ['first_optimization', 'streak_7'],
    trend: 'up',
    trendAmount: 2,
  },
  {
    rank: 3,
    userId: '3',
    username: 'edge_cutter',
    avatar: 'EC',
    score: 11200,
    optimizations: 58,
    streak: 5,
    achievements: ['first_optimization', 'top_10'],
    trend: 'down',
    trendAmount: 1,
  },
  {
    rank: 4,
    userId: '4',
    username: 'network_ninja',
    avatar: 'NN',
    score: 9850,
    optimizations: 45,
    streak: 12,
    achievements: ['first_optimization', 'streak_7'],
    trend: 'up',
    trendAmount: 3,
  },
  {
    rank: 5,
    userId: '5',
    username: 'service_sage',
    avatar: 'SS',
    score: 8700,
    optimizations: 42,
    streak: 3,
    achievements: ['first_optimization'],
    trend: 'same',
    trendAmount: 0,
  },
  {
    rank: 6,
    userId: '6',
    username: 'latency_lord',
    avatar: 'LL',
    score: 7500,
    optimizations: 38,
    streak: 6,
    achievements: ['first_optimization'],
    trend: 'up',
    trendAmount: 1,
  },
  {
    rank: 7,
    userId: '7',
    username: 'path_finder',
    avatar: 'PF',
    score: 6200,
    optimizations: 32,
    streak: 2,
    achievements: ['first_optimization'],
    trend: 'down',
    trendAmount: 2,
  },
  {
    rank: 8,
    userId: '8',
    username: 'cluster_chief',
    avatar: 'CC',
    score: 5100,
    optimizations: 28,
    streak: 4,
    achievements: ['first_optimization'],
    trend: 'up',
    trendAmount: 1,
  },
  {
    rank: 9,
    userId: '9',
    username: 'demo_user',
    avatar: 'DU',
    score: 4200,
    optimizations: 22,
    streak: 1,
    achievements: ['first_optimization'],
    trend: 'up',
    trendAmount: 5,
  },
  {
    rank: 10,
    userId: '10',
    username: 'micro_master',
    avatar: 'MM',
    score: 3800,
    optimizations: 18,
    streak: 0,
    achievements: [],
    trend: 'down',
    trendAmount: 1,
  },
]

const allAchievements: Achievement[] = [
  {
    id: 'first_optimization',
    name: 'First Steps',
    description: 'Complete your first topology optimization',
    icon: '🎯',
    rarity: 'common',
    unlockedAt: '2024-01-15',
  },
  {
    id: 'streak_7',
    name: 'On Fire',
    description: 'Maintain a 7-day optimization streak',
    icon: '🔥',
    rarity: 'rare',
    progress: 5,
    maxProgress: 7,
  },
  {
    id: 'top_10',
    name: 'Rising Star',
    description: 'Reach the top 10 on the leaderboard',
    icon: '⭐',
    rarity: 'epic',
    unlockedAt: '2024-01-20',
  },
  {
    id: 'hundred_optimizations',
    name: 'Century Club',
    description: 'Complete 100 topology optimizations',
    icon: '💯',
    rarity: 'legendary',
    progress: 22,
    maxProgress: 100,
  },
  {
    id: 'perfect_score',
    name: 'Perfectionist',
    description: 'Achieve 50%+ improvement in a single optimization',
    icon: '💎',
    rarity: 'legendary',
    progress: 0,
    maxProgress: 1,
  },
  {
    id: 'early_adopter',
    name: 'Early Adopter',
    description: 'Join during the beta period',
    icon: '🚀',
    rarity: 'rare',
    unlockedAt: '2024-01-01',
  },
]

const rarityColors = {
  common: 'from-slate-400 to-slate-500',
  rare: 'from-blue-400 to-blue-600',
  epic: 'from-purple-400 to-purple-600',
  legendary: 'from-amber-400 to-orange-600',
}

const rarityBorders = {
  common: 'border-slate-500/30',
  rare: 'border-blue-500/30',
  epic: 'border-purple-500/30',
  legendary: 'border-amber-500/30',
}

export default function Leaderboard() {
  const { userScore } = useStore()
  const [timeFilter, setTimeFilter] = useState<'daily' | 'weekly' | 'monthly' | 'allTime'>('weekly')
  const [selectedTab, setSelectedTab] = useState<'leaderboard' | 'achievements'>('leaderboard')
  const [leaderboard, setLeaderboard] = useState(mockLeaderboard)

  // Simulate updating user's score in leaderboard
  useEffect(() => {
    setLeaderboard((prev) =>
      prev.map((entry) =>
        entry.userId === '9' ? { ...entry, score: userScore } : entry
      )
    )
  }, [userScore])

  // Sort and re-rank after score update
  const sortedLeaderboard = [...leaderboard]
    .sort((a, b) => b.score - a.score)
    .map((entry, index) => ({ ...entry, rank: index + 1 }))

  const currentUserRank = sortedLeaderboard.find((e) => e.userId === '9')?.rank || 0
  const currentUserEntry = sortedLeaderboard.find((e) => e.userId === '9')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-bold text-white">Leaderboard</h1>
          <p className="text-slate-400 mt-1">
            Compete with other developers and earn achievements
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-800/50 rounded-xl p-1">
            {(['leaderboard', 'achievements'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setSelectedTab(tab)}
                className={cn(
                  'px-4 py-2 rounded-lg text-sm font-medium transition-colors capitalize',
                  selectedTab === tab
                    ? 'bg-edge-500/20 text-edge-400'
                    : 'text-slate-400 hover:text-white'
                )}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* User Stats Banner */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-6 bg-gradient-to-r from-edge-500/10 to-neural-500/10 border-edge-500/30"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-edge-500 to-neural-500 flex items-center justify-center text-2xl font-bold text-white">
              DU
            </div>
            <div>
              <h2 className="text-2xl font-display font-bold text-white">demo_user</h2>
              <div className="flex items-center gap-4 mt-1">
                <span className="text-slate-400">
                  Rank #{currentUserRank}
                </span>
                <span className="text-slate-400">•</span>
                <span className="text-edge-400 font-semibold">
                  {userScore.toLocaleString()} points
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-8">
            <div className="text-center">
              <p className="text-3xl font-display font-bold text-white">
                {currentUserEntry?.optimizations || 0}
              </p>
              <p className="text-sm text-slate-400">Optimizations</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-display font-bold text-white flex items-center gap-1">
                {currentUserEntry?.streak || 0}
                <Zap className="w-6 h-6 text-warning-400" />
              </p>
              <p className="text-sm text-slate-400">Day Streak</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-display font-bold text-white">
                {allAchievements.filter((a) => a.unlockedAt).length}
              </p>
              <p className="text-sm text-slate-400">Achievements</p>
            </div>
          </div>
        </div>
      </motion.div>

      <AnimatePresence mode="wait">
        {selectedTab === 'leaderboard' ? (
          <motion.div
            key="leaderboard"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="space-y-6"
          >
            {/* Time Filter */}
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-slate-400" />
              <div className="flex items-center gap-2 bg-slate-800/50 rounded-xl p-1">
                {(['daily', 'weekly', 'monthly', 'allTime'] as const).map((filter) => (
                  <button
                    key={filter}
                    onClick={() => setTimeFilter(filter)}
                    className={cn(
                      'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                      timeFilter === filter
                        ? 'bg-edge-500/20 text-edge-400'
                        : 'text-slate-400 hover:text-white'
                    )}
                  >
                    {filter === 'allTime' ? 'All Time' : filter.charAt(0).toUpperCase() + filter.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* Top 3 Podium */}
            <div className="grid grid-cols-3 gap-4">
              {/* Second Place */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="glass-card p-6 text-center mt-8"
              >
                <div className="relative inline-block mb-4">
                  <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-slate-400 to-slate-500 flex items-center justify-center text-2xl font-bold text-white mx-auto">
                    {sortedLeaderboard[1]?.avatar}
                  </div>
                  <div className="absolute -top-2 -right-2 w-8 h-8 bg-slate-400 rounded-full flex items-center justify-center">
                    <Medal className="w-5 h-5 text-white" />
                  </div>
                </div>
                <p className="font-semibold text-white">{sortedLeaderboard[1]?.username}</p>
                <p className="text-2xl font-display font-bold text-slate-300 mt-1">
                  {sortedLeaderboard[1]?.score.toLocaleString()}
                </p>
                <p className="text-sm text-slate-400">2nd Place</p>
              </motion.div>

              {/* First Place */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-card p-6 text-center border-2 border-amber-500/30 bg-gradient-to-b from-amber-500/10 to-transparent"
              >
                <div className="relative inline-block mb-4">
                  <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-amber-400 to-orange-600 flex items-center justify-center text-3xl font-bold text-white mx-auto">
                    {sortedLeaderboard[0]?.avatar}
                  </div>
                  <div className="absolute -top-3 -right-3 w-10 h-10 bg-amber-500 rounded-full flex items-center justify-center">
                    <Crown className="w-6 h-6 text-white" />
                  </div>
                </div>
                <p className="font-semibold text-white text-lg">{sortedLeaderboard[0]?.username}</p>
                <p className="text-3xl font-display font-bold text-amber-400 mt-1">
                  {sortedLeaderboard[0]?.score.toLocaleString()}
                </p>
                <p className="text-sm text-amber-400/80">1st Place</p>
                <div className="mt-3 flex items-center justify-center gap-1">
                  <Zap className="w-4 h-4 text-warning-400" />
                  <span className="text-sm text-slate-300">
                    {sortedLeaderboard[0]?.streak} day streak
                  </span>
                </div>
              </motion.div>

              {/* Third Place */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="glass-card p-6 text-center mt-8"
              >
                <div className="relative inline-block mb-4">
                  <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-amber-600 to-amber-800 flex items-center justify-center text-2xl font-bold text-white mx-auto">
                    {sortedLeaderboard[2]?.avatar}
                  </div>
                  <div className="absolute -top-2 -right-2 w-8 h-8 bg-amber-700 rounded-full flex items-center justify-center">
                    <Award className="w-5 h-5 text-white" />
                  </div>
                </div>
                <p className="font-semibold text-white">{sortedLeaderboard[2]?.username}</p>
                <p className="text-2xl font-display font-bold text-amber-600 mt-1">
                  {sortedLeaderboard[2]?.score.toLocaleString()}
                </p>
                <p className="text-sm text-slate-400">3rd Place</p>
              </motion.div>
            </div>

            {/* Full Leaderboard */}
            <div className="glass-card p-6">
              <h2 className="text-xl font-semibold text-white mb-4">Full Rankings</h2>
              <div className="space-y-2">
                {sortedLeaderboard.slice(3).map((entry, index) => (
                  <motion.div
                    key={entry.userId}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className={cn(
                      'flex items-center justify-between p-4 rounded-xl transition-colors',
                      entry.userId === '9'
                        ? 'bg-edge-500/10 border border-edge-500/30'
                        : 'bg-slate-800/30 hover:bg-slate-800/50'
                    )}
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 text-center">
                        <span
                          className={cn(
                            'text-lg font-bold',
                            entry.rank <= 10 ? 'text-white' : 'text-slate-400'
                          )}
                        >
                          #{entry.rank}
                        </span>
                      </div>
                      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-slate-600 to-slate-700 flex items-center justify-center text-lg font-bold text-white">
                        {entry.avatar}
                      </div>
                      <div>
                        <p className="font-medium text-white">{entry.username}</p>
                        <p className="text-sm text-slate-400">
                          {entry.optimizations} optimizations
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      <div className="flex items-center gap-1">
                        <Zap className="w-4 h-4 text-warning-400" />
                        <span className="text-sm text-slate-300">{entry.streak}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {entry.trend === 'up' && (
                          <span className="text-success-400 text-sm flex items-center">
                            <TrendingUp className="w-4 h-4 mr-1" />+{entry.trendAmount}
                          </span>
                        )}
                        {entry.trend === 'down' && (
                          <span className="text-danger-400 text-sm flex items-center">
                            <TrendingUp className="w-4 h-4 mr-1 rotate-180" />-{entry.trendAmount}
                          </span>
                        )}
                      </div>
                      <p className="text-xl font-display font-bold text-white w-24 text-right">
                        {entry.score.toLocaleString()}
                      </p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="achievements"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            {/* Achievement Stats */}
            <div className="grid grid-cols-4 gap-4">
              {(['common', 'rare', 'epic', 'legendary'] as const).map((rarity) => {
                const total = allAchievements.filter((a) => a.rarity === rarity).length
                const unlocked = allAchievements.filter(
                  (a) => a.rarity === rarity && a.unlockedAt
                ).length
                return (
                  <div
                    key={rarity}
                    className={cn('glass-card p-4 border', rarityBorders[rarity])}
                  >
                    <div
                      className={cn(
                        'w-10 h-10 rounded-xl bg-gradient-to-br flex items-center justify-center mb-3',
                        rarityColors[rarity]
                      )}
                    >
                      <Star className="w-5 h-5 text-white" />
                    </div>
                    <p className="text-white font-medium capitalize">{rarity}</p>
                    <p className="text-2xl font-display font-bold text-white mt-1">
                      {unlocked}/{total}
                    </p>
                  </div>
                )
              })}
            </div>

            {/* Achievement Grid */}
            <div className="glass-card p-6">
              <h2 className="text-xl font-semibold text-white mb-4">All Achievements</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {allAchievements.map((achievement, index) => {
                  const isUnlocked = !!achievement.unlockedAt
                  return (
                    <motion.div
                      key={achievement.id}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: index * 0.05 }}
                      className={cn(
                        'p-4 rounded-xl border transition-all',
                        isUnlocked
                          ? `bg-gradient-to-br ${rarityColors[achievement.rarity]}/10 ${rarityBorders[achievement.rarity]}`
                          : 'bg-slate-800/30 border-slate-700/50 opacity-60'
                      )}
                    >
                      <div className="flex items-start gap-3">
                        <div
                          className={cn(
                            'w-12 h-12 rounded-xl flex items-center justify-center text-2xl',
                            isUnlocked
                              ? `bg-gradient-to-br ${rarityColors[achievement.rarity]}`
                              : 'bg-slate-700'
                          )}
                        >
                          {isUnlocked ? achievement.icon : '🔒'}
                        </div>
                        <div className="flex-1">
                          <p className="font-medium text-white">{achievement.name}</p>
                          <p className="text-sm text-slate-400 mt-0.5">
                            {achievement.description}
                          </p>
                          {achievement.progress !== undefined && !isUnlocked && (
                            <div className="mt-2">
                              <div className="flex items-center justify-between text-xs mb-1">
                                <span className="text-slate-400">Progress</span>
                                <span className="text-white">
                                  {achievement.progress}/{achievement.maxProgress}
                                </span>
                              </div>
                              <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                                <div
                                  className={cn(
                                    'h-full rounded-full bg-gradient-to-r',
                                    rarityColors[achievement.rarity]
                                  )}
                                  style={{
                                    width: `${(achievement.progress! / achievement.maxProgress!) * 100}%`,
                                  }}
                                />
                              </div>
                            </div>
                          )}
                          {isUnlocked && (
                            <p className="text-xs text-slate-500 mt-2">
                              Unlocked {achievement.unlockedAt}
                            </p>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  )
                })}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
