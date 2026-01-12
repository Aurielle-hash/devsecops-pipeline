package com.babyfoot.service;

import com.babyfoot.model.Match;
import com.babyfoot.repository.MatchRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Service
public class MatchService {

    @Autowired
    private MatchRepository matchRepository;

    @Autowired
    private PlayerService playerService;

    public List<Match> getAllMatches() {
        return matchRepository.findByOrderByCreatedAtDesc();
    }

    public Optional<Match> getMatchById(Long id) {
        return matchRepository.findById(id);
    }

    public List<Match> getMatchesByPlayer(String playerName) {
        return matchRepository.findByPlayer(playerName);
    }

    public List<Match> getActiveMatches() {
        return matchRepository.findByStatus(Match.MatchStatus.IN_PROGRESS);
    }

    public Match createMatch(Match match) {
        // Ensure players exist
        playerService.getPlayerByName(match.getPlayer1())
                .orElseGet(() -> playerService.createPlayer(new com.babyfoot.model.Player(match.getPlayer1())));
        playerService.getPlayerByName(match.getPlayer2())
                .orElseGet(() -> playerService.createPlayer(new com.babyfoot.model.Player(match.getPlayer2())));

        match.setCreatedAt(LocalDateTime.now());
        match.setStatus(Match.MatchStatus.IN_PROGRESS);
        return matchRepository.save(match);
    }

    public Match updateScore(Long id, int score1, int score2) {
        Match match = matchRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Match not found with id: " + id));

        match.setScore1(score1);
        match.setScore2(score2);

        return matchRepository.save(match);
    }

    public Match finishMatch(Long id) {
        Match match = matchRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Match not found with id: " + id));

        match.setStatus(Match.MatchStatus.FINISHED);
        match.setFinishedAt(LocalDateTime.now());

        // Update player statistics
        String winner = match.getWinner();
        if (winner != null && !winner.equals("Draw")) {
            if (winner.equals(match.getPlayer1())) {
                playerService.updatePlayerStats(match.getPlayer1(), true, match.getScore1(), match.getScore2());
                playerService.updatePlayerStats(match.getPlayer2(), false, match.getScore2(), match.getScore1());
            } else {
                playerService.updatePlayerStats(match.getPlayer2(), true, match.getScore2(), match.getScore1());
                playerService.updatePlayerStats(match.getPlayer1(), false, match.getScore1(), match.getScore2());
            }
        }

        return matchRepository.save(match);
    }

    public void deleteMatch(Long id) {
        matchRepository.deleteById(id);
    }
}