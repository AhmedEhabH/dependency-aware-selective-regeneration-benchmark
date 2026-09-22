# WP-1b MAIN_297 - exploratory analyses X1-X11 (never primary)

Computed after the primary result was frozen and tagged. None of these results can change the primary verdict.

## X6 escalation frontier (RM-CSS -> Agent cascade)

- preregistered reading: `ESCALATION_NO_GAIN`
- RM-CSS F1 0.3568; at 20% escalation (U1): REPLACE -0.0188 [-0.0395, +0.0008] (p vs random 0.9950024987506247); UNION +0.0046 [-0.0046, +0.0149] (p vs random 0.7471264367816092)
- gain capture at 20%: 0.1289865348971684

| fraction | U1-REPLACE F1 | U1-UNION F1 | random mean (REPLACE) | USD/task (U1-REPLACE) |
|---:|---:|---:|---:|---:|
| 0.00 | 0.3568 | 0.3568 | 0.3568 | 0.00531 |
| 0.05 | 0.3558 | 0.3608 | 0.3570 | 0.00671 |
| 0.10 | 0.3463 | 0.3627 | 0.3572 | 0.00799 |
| 0.15 | 0.3457 | 0.3608 | 0.3573 | 0.00928 |
| 0.20 | 0.3380 | 0.3614 | 0.3577 | 0.01039 |
| 0.25 | 0.3353 | 0.3579 | 0.3581 | 0.01178 |
| 0.30 | 0.3381 | 0.3625 | 0.3585 | 0.01292 |
| 0.35 | 0.3356 | 0.3626 | 0.3587 | 0.01419 |
| 0.40 | 0.3467 | 0.3730 | 0.3590 | 0.01528 |
| 0.45 | 0.3506 | 0.3766 | 0.3592 | 0.01660 |
| 0.50 | 0.3511 | 0.3777 | 0.3595 | 0.01776 |
| 0.55 | 0.3496 | 0.3796 | 0.3600 | 0.01893 |
| 0.60 | 0.3505 | 0.3820 | 0.3602 | 0.02013 |
| 0.65 | 0.3526 | 0.3841 | 0.3606 | 0.02127 |
| 0.70 | 0.3563 | 0.3880 | 0.3607 | 0.02250 |
| 0.75 | 0.3547 | 0.3865 | 0.3612 | 0.02364 |
| 0.80 | 0.3546 | 0.3862 | 0.3616 | 0.02471 |
| 0.85 | 0.3545 | 0.3868 | 0.3620 | 0.02592 |
| 0.90 | 0.3554 | 0.3866 | 0.3624 | 0.02700 |
| 0.95 | 0.3569 | 0.3878 | 0.3628 | 0.02819 |
| 1.00 | 0.3631 | 0.3925 | 0.3631 | 0.02936 |

## X3 band teacher ceiling

- reading: `NO_TEACHER_HEADROOM`
- [0.10,0.35): hybrid − RM-CSS +0.0291 (Q5 +0.0119)

## X10 zero-generative dense anchor

- size-matched dense top-k F1 0.2781 (minus RM-CSS -0.0787)

## X2 / X4 / X11

- gold in RM-CSS pool 0.746; agent recall inside 0.406 / outside 0.060
- gold read-but-not-selected 0.014; surfaced-not-selected 0.201
- non-consecutive duplicate tool requests 0.127; zero-result searches 0.427 (multi-word 0.686)

