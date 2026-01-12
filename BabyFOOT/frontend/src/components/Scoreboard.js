import React, { useState, useEffect } from 'react'
import { matchesAPI } from '../services/api'
import { apm } from '../apm'

const Scoreboard = ({ refreshTrigger }) => {
    const [activeMatches, setActiveMatches] = useState([])
    const [finishedMatches, setFinishedMatches] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        loadMatches()
    }, [refreshTrigger])

    const loadMatches = async () => {
        try {
            setLoading(true)
            const [activeResponse, allResponse] = await Promise.all([
                matchesAPI.getActive(),
                matchesAPI.getAll()
            ])

            setActiveMatches(activeResponse.data)
            setFinishedMatches(allResponse.data.filter(match => match.status === 'FINISHED'))
            setError(null)
        } catch (err) {
            setError('Erreur lors du chargement des matchs')
            apm.captureError(err)
        } finally {
            setLoading(false)
        }
    }

    const handleScoreUpdate = async (matchId, player, increment) => {
        try {
            const match = activeMatches.find(m => m.id === matchId)
            if (!match) return

            const newScore1 = player === 1 ? Math.max(0, match.score1 + increment) : match.score1
            const newScore2 = player === 2 ? Math.max(0, match.score2 + increment) : match.score2

            await matchesAPI.updateScore(matchId, newScore1, newScore2)
            loadMatches()

            apm.addLabels({
                action: 'score_updated',
                match_id: matchId,
                player: player,
                increment: increment
            })
        } catch (err) {
            setError('Erreur lors de la mise à jour du score')
            apm.captureError(err)
        }
    }

    const handleFinishMatch = async (matchId) => {
        if (!window.confirm('Êtes-vous sûr de vouloir terminer ce match ?')) return

        try {
            await matchesAPI.finish(matchId)
            loadMatches()
            apm.addLabels({ action: 'match_finished', match_id: matchId })
        } catch (err) {
            setError('Erreur lors de la finalisation du match')
            apm.captureError(err)
        }
    }

    const handleDeleteMatch = async (matchId) => {
        if (!window.confirm('Êtes-vous sûr de vouloir supprimer ce match ?')) return

        try {
            await matchesAPI.delete(matchId)
            loadMatches()
            apm.addLabels({ action: 'match_deleted', match_id: matchId })
        } catch (err) {
            setError('Erreur lors de la suppression du match')
            apm.captureError(err)
        }
    }

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    const getWinnerDisplay = (match) => {
        if (match.status !== 'FINISHED') return null

        if (match.score1 > match.score2) {
            return `🏆 ${match.player1} remporte le match !`
        } else if (match.score2 > match.score1) {
            return `🏆 ${match.player2} remporte le match !`
        } else {
            return '🤝 Match nul !'
        }
    }

    if (loading) return <div className="loading">Chargement des matchs...</div>

    return (
        <div className="scoreboard">
            <h2>📊 Tableau des Scores</h2>

            {error && <div className="error">{error}</div>}


            {/* Matchs en cours */}
            <div className="active-matches">
                <h3>⚡ Matchs en cours</h3>
                {activeMatches.length > 0 ? (
                    <div className="matches-list">
                        {activeMatches.map(match => (
                            <div key={match.id} className="match-card active">
                                <div className="match-header">
                                    <span className="match-date">{formatDate(match.createdAt)}</span>
                                    <span className="match-status in_progress">En cours</span>
                                </div>

                                <div className="score-control">
                                    <div className="player-score">
                                        <h3>{match.player1}</h3>
                                        <div className="score-buttons">
                                            <button
                                                className="btn btn-secondary btn-small"
                                                onClick={() => handleScoreUpdate(match.id, 1, -1)}
                                                disabled={match.score1 === 0}
                                            >
                                                -
                                            </button>
                                            <span className="score">{match.score1}</span>
                                            <button
                                                className="btn btn-primary btn-small"
                                                onClick={() => handleScoreUpdate(match.id, 1, 1)}
                                            >
                                                +
                                            </button>
                                        </div>
                                    </div>

                                    <div className="vs">VS</div>

                                    <div className="player-score">
                                        <h3>{match.player2}</h3>
                                        <div className="score-buttons">
                                            <button
                                                className="btn btn-secondary btn-small"
                                                onClick={() => handleScoreUpdate(match.id, 2, -1)}
                                                disabled={match.score2 === 0}
                                            >
                                                -
                                            </button>
                                            <span className="score">{match.score2}</span>
                                            <button
                                                className="btn btn-primary btn-small"
                                                onClick={() => handleScoreUpdate(match.id, 2, 1)}
                                            >
                                                +
                                            </button>
                                        </div>
                                    </div>
                                </div>

                                <div className="match-actions">
                                    <button
                                        className="btn btn-success"
                                        onClick={() => handleFinishMatch(match.id)}
                                    >
                                        Terminer le Match
                                    </button>
                                    <button
                                        className="btn btn-danger"
                                        onClick={() => handleDeleteMatch(match.id)}
                                    >
                                        Supprimer
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="no-matches">
                        Aucun match en cours. Créez un nouveau match pour commencer !
                    </div>
                )}
            </div>

            {/* Historique des matchs */}
            <div className="match-history">
                <h3>📚 Historique des Matchs</h3>
                {finishedMatches.length > 0 ? (
                    <div className="matches-list">
                        {finishedMatches.slice(0, 10).map(match => (
                            <div key={match.id} className="match-card finished">
                                <div className="match-header">
                                    <span className="match-date">{formatDate(match.createdAt)}</span>
                                    <span className="match-status finished">Terminé</span>
                                </div>

                                <div className="match-score">
                                    <div className="player">
                                        <span className="player-name">{match.player1}</span>
                                        <span className={`score ${match.score1 > match.score2 ? 'winner' : ''}`}>
                      {match.score1}
                    </span>
                                    </div>
                                    <div className="vs">VS</div>
                                    <div className="player">
                                        <span className="player-name">{match.player2}</span>
                                        <span className={`score ${match.score2 > match.score1 ? 'winner' : ''}`}>
                      {match.score2}
                    </span>
                                    </div>
                                </div>

                                <div className={match.score1 === match.score2 ? 'draw' : 'winner'}>
                                    {getWinnerDisplay(match)}
                                </div>

                                <div className="match-actions">
                                    <button
                                        className="btn btn-danger btn-small"
                                        onClick={() => handleDeleteMatch(match.id)}
                                    >
                                        Supprimer
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="no-matches">
                        Aucun match terminé pour le moment.
                    </div>
                )}
            </div>
        </div>
    )
}

export default Scoreboard