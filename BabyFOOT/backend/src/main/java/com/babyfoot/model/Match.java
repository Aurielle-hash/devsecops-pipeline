package com.babyfoot.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import java.time.LocalDateTime;

@Data
@Entity
@NoArgsConstructor
@AllArgsConstructor
@Table(name = "matches")
public class Match {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "player1", nullable = false)
    private String player1;

    @Column(name = "player2", nullable = false)
    private String player2;

    @Column(name = "score1", columnDefinition = "integer default 0")
    private int score1 = 0;

    @Column(name = "score2", columnDefinition = "integer default 0")
    private int score2 = 0;

    @Column(name = "status")
    @Enumerated(EnumType.STRING)
    private MatchStatus status = MatchStatus.IN_PROGRESS;

    @Column(name = "created_at")
    private LocalDateTime createdAt = LocalDateTime.now();

    @Column(name = "finished_at")
    private LocalDateTime finishedAt;

    public enum MatchStatus {
        IN_PROGRESS, FINISHED, CANCELLED
    }

    public String getWinner() {
        if (status != MatchStatus.FINISHED) return null;
        if (score1 > score2) return player1;
        if (score2 > score1) return player2;
        return "Draw";
    }
}