package com.babyfoot.service;

import com.babyfoot.model.Player;
import com.babyfoot.repository.PlayerRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.Optional;

@Service
public class PlayerService {

    @Autowired
    private PlayerRepository playerRepository;

    public List<Player> getAllPlayers() {
        return playerRepository.findAll();
    }

    public Optional<Player> getPlayerById(Long id) {
        return playerRepository.findById(id);
    }

    public Optional<Player> getPlayerByName(String name) {
        return playerRepository.findByName(name);
    }

    public Player createPlayer(Player player) {
        if (playerRepository.existsByName(player.getName())) {
            throw new RuntimeException("Player with name " + player.getName() + " already exists");
        }
        return playerRepository.save(player);
    }

    public Player updatePlayer(Long id, Player playerDetails) {
        Player player = playerRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Player not found with id: " + id));

        player.setName(playerDetails.getName());
        player.setWins(playerDetails.getWins());
        player.setLosses(playerDetails.getLosses());
        player.setGoalsScored(playerDetails.getGoalsScored());
        player.setGoalsConceded(playerDetails.getGoalsConceded());

        return playerRepository.save(player);
    }

    public void deletePlayer(Long id) {
        playerRepository.deleteById(id);
    }

    public void updatePlayerStats(String playerName, boolean won, int goalsScored, int goalsConceded) {
        Optional<Player> playerOpt = playerRepository.findByName(playerName);
        if (playerOpt.isPresent()) {
            Player player = playerOpt.get();
            if (won) {
                player.setWins(player.getWins() + 1);
            } else {
                player.setLosses(player.getLosses() + 1);
            }
            player.setGoalsScored(player.getGoalsScored() + goalsScored);
            player.setGoalsConceded(player.getGoalsConceded() + goalsConceded);
            playerRepository.save(player);
        }
    }
}