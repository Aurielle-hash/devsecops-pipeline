import React, { useState, useEffect } from 'react'
import { playersAPI } from '../services/api'
import { apm } from '../apm'

const PlayerList = () => {
    const [players, setPlayers] = useState([])
    const [newPlayerName, setNewPlayerName] = useState('')
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        loadPlayers()
    }, [])

    const loadPlayers = async () => {
        try {
            setLoading(true)
            const response = await playersAPI.getAll()
            setPlayers(response.data)
            setError(null)
        } catch (err) {
            setError('Erreur lors du chargement des joueurs')
            apm.captureError(err)
        } finally {
            setLoading(false)
        }
    }

    const handleAddPlayer = async (e) => {
        e.preventDefault()
        if (!newPlayerName.trim()) return

        try {
            await playersAPI.create({ name: newPlayerName.trim() })
            setNewPlayerName('')
            loadPlayers()
            apm.addLabels({ action: 'player_created', player_name: newPlayerName })
        } catch (err) {
            setError('Erreur lors de la création du joueur')
            apm.captureError(err)
        }
    }

    const handleDeletePlayer = async (id) => {
        if (!window.confirm('Êtes-vous sûr de vouloir supprimer ce joueur ?')) return

        try {
            await playersAPI.delete(id)
            loadPlayers()
            apm.addLabels({ action: 'player_deleted', player_id: id })
        } catch (err) {
            setError('Erreur lors de la suppression du joueur')
            apm.captureError(err)
        }
    }

    if (loading) return <div className="loading">Chargement des joueurs...</div>

    return (
        <div className="player-list">
            <h2>🏆 Joueurs</h2>

            {error && <div className="error">{error}</div>
            }

            <form onSubmit={handleAddPlayer} className="add-player-form">
                <input
                    type="text"
                    value={newPlayerName}
                    onChange={(e) => setNewPlayerName(e.target.value)}
                    placeholder="Nom du nouveau joueur"
                    className="player-input"
                />
                <button type="submit" className="btn btn-primary">
                    Ajouter Joueur
                </button>
            </form>

            <div className="players-grid">
                {players.map(player => (
                    <div key={player.id} className="player-card">
                        <div className="player-header">
                            <h3>{player.name}</h3>
                            <button
                                onClick={() => handleDeletePlayer(player.id)}
                                className="btn btn-danger btn-small"
                            >
                                ✕
                            </button>
                        </div>
                        <div className="player-stats">
                            <div className="stat">
                                <span className="stat-label">Victoires:</span>
                                <span className="stat-value wins">{player.wins}</span>
                            </div>
                            <div className="stat">
                                <span className="stat-label">Défaites:</span>
                                <span className="stat-value losses">{player.losses}</span>
                            </div>
                            <div className="stat">
                                <span className="stat-label">Buts marqués:</span>
                                <span className="stat-value">{player.goalsScored}</span>
                            </div>
                            <div className="stat">
                                <span className="stat-label">Buts encaissés:</span>
                                <span className="stat-value">{player.goalsConceded}</span>
                            </div>
                            <div className="stat">
                                <span className="stat-label">Ratio:</span>
                                <span className="stat-value ratio">
                  {player.wins + player.losses > 0
                      ? (player.wins / (player.wins + player.losses) * 100).toFixed(1) + '%'
                      : '0%'
                  }
                </span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {players.length === 0 && !loading && (
                <div className="no-players">
                    Aucun joueur enregistré. Ajoutez votre premier joueur !
                </div>
            )}
        </div>
    )
}

export default PlayerList