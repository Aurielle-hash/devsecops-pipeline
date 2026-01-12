package com.babyfoot.repository;

import com.babyfoot.model.Match;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface MatchRepository extends JpaRepository<Match, Long> {
    List<Match> findByOrderByCreatedAtDesc();

    @Query("SELECT m FROM Match m WHERE m.player1 = ?1 OR m.player2 = ?1")
    List<Match> findByPlayer(String playerName);

    List<Match> findByStatus(Match.MatchStatus status);
}