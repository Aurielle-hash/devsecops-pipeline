import React, { useState, useEffect } from 'react'
import { matchesAPI, playersAPI } from '../services/api'
import { apm } from '../apm'

const MatchForm = ({ onMatchCreated }) => {
    const [players, setPlayers] = useState([])
    const [player1, setPlayer1] = useState('')
    const [player2, setPlayer2] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    useEffect(() => {
        loadPlayers()
    }, [])

    const loadPlayers = async () => {
        try {
            const response = await playersAPI.getAll()
            setPlayers(response.data)
        } catch (err) {
            setError('Erreur lors du chargement des joueurs')
            apm.captureError(err)
        }
    }

    const handleSubmit = async (e) => {
        e.preventDefault()

        if (!player1 || !player2) {
            setError('Veuillez sélectionner deux joueurs')
            return
        }

        if (player1 === player2) {
            setError('Veuillez sélectionner deux joueurs différents')
            return
        }

        try {
            setLoading(true)
            setError(null)

            const newMatch = {
                player1,
                player2,
                score1: 0,
                score2: 0
            }

            const response = await matchesAPI.create(newMatch)

            // Reset form
            setPlayer1('')
            setPlayer2('')

            // Notify parent component
            if (onMatchCreated) {
                onMatchCreated(response.data)
            }

            apm.addLabels({
                action: 'match_created',
                player1: player1,
                player2: player2
            })

        } catch (err) {
            setError('Erreur lors de la création du match')
            apm.captureError(err)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="match-form">
            <h2>⚽ Nouveau Match</h2>

            {error && <div className="error">{error}</div>
            }

            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label htmlFor="player1">Joueur 1:</label>
                    <select
                        id="player1"
                        value={player1}
                        onChange={(e) => setPlayer1(e.target.value)}
                        className="form-select"
                        disabled={loading}
                    >
                        <option value="">Sélectionner un joueur</option>
                        {players.map(player => (
                            <option key={player.id} value={player.name}>
                                {player.name}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="vs-divider">VS</div>

                <div className="form-group">
                    <label htmlFor="player2">Joueur 2:</label>
                    <select
                        id="player2"
                        value={player2}
                        onChange={(e) => setPlayer2(e.target.value)}
                        className="form-select"
                        disabled={loading}
                    >
                        <option value="">Sélectionner un joueur</option>
                        {players.map(player => (
                            <option key={player.id} value={player.name}>
                                {player.name}
                            </option>
                        ))}
                    </select>
                </div>

                <button
                    type="submit"
                    className="btn btn-primary btn-large"
                    disabled={loading || !player1 || !player2 || player1 === player2}
                >
                    {loading ? 'Création...' : 'Commencer le Match'}
                </button>
            </form>

            {players.length === 0 && (
                <div className="info">
                    Vous devez d'abord créer des joueurs pour commencer un match.
                </div>
            )}
        </div>
    )
}

export default MatchForm