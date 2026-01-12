package com.babyfoot.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

@Data
@Entity
@NoArgsConstructor
@AllArgsConstructor
@Table(name = "players")
public class Player {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String name;

    @Column(name = "wins", columnDefinition = "integer default 0")
    private int wins = 0;

    @Column(name = "losses", columnDefinition = "integer default 0")
    private int losses = 0;

    @Column(name = "goals_scored", columnDefinition = "integer default 0")
    private int goalsScored = 0;

    @Column(name = "goals_conceded", columnDefinition = "integer default 0")
    private int goalsConceded = 0;

    public Player(String name) {
        this.name = name;
    }
}