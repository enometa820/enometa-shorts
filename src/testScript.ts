import { VisualScript } from "./types";

// Phase 0 프로토타입 테스트 대본
// "우리는 하루에 6만 개의 생각을 한다" 시리즈
export const testVisualScript: VisualScript = {
  global: {
    color_palette: ["#00D4FF", "#1A1A2E", "#FF6B35", "#E8E8E8"],
    background_color: "#0A0A0F",
    particle_total: 2000, // 프로토타입: 성능을 위해 축소
    font: "Pretendard Variable",
    palette: "phantom",
  },

  scenes: [
    {
      id: "scene_01",
      sentence: "우리는 하루에 6만 개의 생각을 한다",
      start_sec: 0.0,
      end_sec: 6.0,
      emotion: "neutral_curious",
      layers: {
        semantic: [
          {
            vocab: "particle_birth",
            params: {
              count: 2000,
              spawn_duration_sec: 4.0,
              spawn_pattern: "random_positions",
              initial_color: "#8B5CF6",
              initial_opacity: 0.6,
              size_range: [1, 3],
            },
          },
          {
            vocab: "counter_up",
            params: {
              target: 60000,
              position: "center",
              font_size: 120,
              color: "#FFFFFF",
              fade_out_at_end: true,
            },
          },
        ],
        audio_reactive: {
          particle_size: "bass * 3",
          particle_brightness: "rms * 0.7 + 0.3",
          glow_intensity: "rms * 15",
          burst_on_onset: true,
        },
        background: {
          vocab: "flow_field_calm",
          params: {
            noise_scale: 0.003,
            speed: 0.1,
            line_opacity: 0.15,
            line_color: "#8B5CF6",
          },
        },
      },
    },

    {
      id: "scene_02",
      sentence: "그중 95%는 어제와 같은 생각이다",
      start_sec: 6.5,
      end_sec: 12.0,
      emotion: "somber",
      layers: {
        semantic: [
          {
            vocab: "particle_split_ratio",
            params: {
              ratio_a: 0.95,
              ratio_b: 0.05,
              transition_duration_sec: 2.0,
              group_a: {
                color: "#555577",
                behavior: "orbit",
                orbit_radius: 300,
                orbit_speed: 0.5,
              },
              group_b: {
                color: "#8B5CF6",
                behavior: "free_wander",
                speed: 1.5,
              },
            },
          },
        ],
        audio_reactive: {
          orbit_radius_mod: "bass * 50",
          orbit_shake: "onset ? 15 : 0",
          group_b_glow: "rms * 20",
        },
        background: {
          vocab: "flow_field_calm",
          params: {
            noise_scale: 0.003,
            speed: 0.05,
            line_opacity: 0.08,
            line_color: "#555577",
          },
        },
      },
    },

    {
      id: "scene_03",
      sentence: "그렇다면 오늘의 나는 어제의 복사본인가?",
      start_sec: 12.5,
      end_sec: 18.0,
      emotion: "tension_question",
      layers: {
        semantic: [
          {
            vocab: "particle_orbit",
            params: {
              count: 1900,
              color: "#555577",
              orbit_radius: 300,
              orbit_speed: 0.5,
            },
          },
          {
            vocab: "brightness_pulse",
            params: {
              rhythm: "tension",
              intensity: 0.3,
              speed: 2.0,
            },
          },
        ],
        audio_reactive: {
          glitch_intensity: "high * 0.8",
          tension_zoom: "rms * 0.05 + 1.0",
        },
        background: {
          vocab: "flow_field_turbulent",
          params: {
            noise_scale: 0.008,
            speed: 0.4,
            line_opacity: 0.2,
            line_color: "#8888AA",
          },
        },
      },
    },

    {
      id: "scene_04",
      sentence: "아니다. 깨어 있다는 것은 반복을 알아차리는 것이다.",
      start_sec: 18.5,
      end_sec: 25.0,
      emotion: "awakening_climax",
      layers: {
        semantic: [
          {
            vocab: "particle_escape",
            params: {
              source: "orbit",
              escape_count: 1,
              escape_speed: 3.0,
              escape_color: "#FFFFFF",
            },
          },
          {
            vocab: "particle_chain_awaken",
            params: {
              awaken_radius: 80,
              awaken_speed: 0.5,
              awaken_color: "#8B5CF6",
              chain_delay_ms: 100,
            },
          },
        ],
        audio_reactive: {
          escape_trigger: "onset",
          chain_speed: "mid * 2",
          glow_intensity: "rms * 30",
          burst_particles_on_onset: true,
        },
        background: {
          vocab: "flow_field_turbulent",
          transition_to: "flow_field_calm",
          params: {
            noise_scale: 0.006,
            speed: 0.3,
            line_opacity: 0.15,
            line_color: "#7C3AED",
          },
        },
      },
    },

    {
      id: "scene_05",
      sentence: "지금 이 순간, 당신은 깨어 있는가?",
      start_sec: 25.5,
      end_sec: 30.0,
      emotion: "transcendent_open",
      layers: {
        semantic: [
          {
            vocab: "particle_scatter",
            params: {
              count: 2000,
              color: "#8B5CF6",
              glow: true,
              expansion_speed: 0.3,
            },
          },
          {
            vocab: "brightness_pulse",
            params: {
              rhythm: "heartbeat",
              intensity: 0.5,
              speed: 1.0,
            },
          },
        ],
        audio_reactive: {
          expansion_rate: "rms * 0.3",
          pulse_intensity: "bass",
          final_glow: "rms * 40",
          fade_with_audio: true,
        },
        background: {
          vocab: "flow_field_calm",
          params: {
            noise_scale: 0.002,
            speed: 0.08,
            line_opacity: 0.1,
            line_color: "#8B5CF6",
          },
        },
      },
    },
  ],

  transitions: {
    default: {
      type: "crossfade",
      duration_sec: 0.5,
    },
    scene_03_to_04: {
      type: "onset_triggered",
      note: "음악 비트에 맞춰 전환 — 클라이맥스 진입",
    },
  },
};
