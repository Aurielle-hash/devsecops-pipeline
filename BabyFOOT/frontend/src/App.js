import React, { useState, useEffect } from 'react'
import PlayerList from './components/PlayerList'
import MatchForm from './components/MatchForm'
import Scoreboard from './components/Scoreboard'
import { apm } from './apm'
import './App.css'

function App() {
    const [activeTab, setActiveTab] = useState('scoreboard')
    const [refreshTrigger, setRefreshTrigger] = useState(0)

    useEffect(() => {
        // Set initial page load name for APM
        apm.setInitialPageLoadName('Babyfoot Dashboard')

        // Add custom labels for APM
        apm.addLabels({
            application: 'babyfoot',
            version: '1.0.0',
            environment: 'development'
        })
    }, [])

    const handleMatchCreated = (newMatch) => {
        // Trigger refresh of scoreboard
        setRefreshTrigger(prev => prev + 1)
        // Switch to scoreboard tab to see the new match
        setActiveTab('scoreboard')

        // Track match creation in APM
        apm.addLabels({
            last_action: 'match_created',
            match_id: newMatch.id
        })
    }

    const handleTabChange = (tab) => {
        setActiveTab(tab)

        // Track navigation in APM
        apm.startTransaction(`Navigate to ${tab}`, 'navigation')
        apm.addLabels({ current_tab: tab })
    }

    return (
        <div className="App">
            <header className="app-header">
                <h1> Babyfoot Championship</h1>
                <p>Gérez vos parties de babyfoot comme un pro !</p>
            </header>

            <nav className="app-nav">
                <button
                    className={`nav-btn ${activeTab === 'scoreboard' ? 'active' : ''}`}
                    onClick={() => handleTabChange('scoreboard')}
                >
                     Scores
                </button>
                <button
                    className={`nav-btn ${activeTab === 'new-match' ? 'active' : ''}`}
                    onClick={() => handleTabChange('new-match')}
                >
                     Nouveau Match
                </button>
                <button
                    className={`nav-btn ${activeTab === 'players' ? 'active' : ''}`}
                    onClick={() => handleTabChange('players')}
                >
                     Joueurs
                </button>
            </nav>

            <main className="app-main">
                {activeTab === 'scoreboard' && (
                    <Scoreboard refreshTrigger={refreshTrigger} />
                )}
                {activeTab === 'new-match' && (
                    <MatchForm onMatchCreated={handleMatchCreated} />
                )}
                {activeTab === 'players' && (
                    <PlayerList />
                )}
            </main>

            <footer className="app-footer">
                <p>
                     Instrumenté avec Elastic APM |
                    Développé avec  pour les passionnés de babyfoot
                </p>
            </footer>
        </div>
    )
}

export default App