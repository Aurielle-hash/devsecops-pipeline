package com.babyfoot.controller;

import com.babyfoot.model.Match;
import com.babyfoot.service.MatchService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/matches")
@CrossOrigin(origins = "*")
public class MatchController {

    @Autowired
    private MatchService matchService;

    @GetMapping
    public List<Match> getAllMatches() {
        return matchService.getAllMatches();
    }

    @GetMapping("/{id}")
    public ResponseEntity<Match> getMatchById(@PathVariable Long id) {
        return matchService.getMatchById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/player/{playerName}")
    public List<Match> getMatchesByPlayer(@PathVariable String playerName) {
        return matchService.getMatchesByPlayer(playerName);
    }

    @GetMapping("/active")
    public List<Match> getActiveMatches() {
        return matchService.getActiveMatches();
    }

    @PostMapping
    public Match createMatch(@RequestBody Match match) {
        return matchService.createMatch(match);
    }

    @PutMapping("/{id}/score")
    public ResponseEntity<Match> updateScore(@PathVariable Long id, @RequestBody ScoreUpdateRequest request) {
        try {
            Match updatedMatch = matchService.updateScore(id, request.getScore1(), request.getScore2());
            return ResponseEntity.ok(updatedMatch);
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }

    @PutMapping("/{id}/finish")
    public ResponseEntity<Match> finishMatch(@PathVariable Long id) {
        try {
            Match finishedMatch = matchService.finishMatch(id);
            return ResponseEntity.ok(finishedMatch);
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteMatch(@PathVariable Long id) {
        matchService.deleteMatch(id);
        return ResponseEntity.ok().build();
    }

    public static class ScoreUpdateRequest {
        private int score1;
        private int score2;

        public int getScore1() { return score1; }
        public void setScore1(int score1) { this.score1 = score1; }
        public int getScore2() { return score2; }
        public void setScore2(int score2) { this.score2 = score2; }
    }
}