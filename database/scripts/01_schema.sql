-- ============================================================
-- VisionCampus - Esquema de la base de datos (PostgreSQL)
-- Archivo: database/scripts/01_schema.sql
--
-- Crea las 4 tablas que usa el sistema:
--   aulas                -> aulas y su capacidad
--   eventos              -> entradas y salidas de personas
--   ocupacion_historico  -> ocupación del aula, medida cada pocos segundos
--   rostros_registrados  -> rostros de voluntarios (con su consentimiento)
--
-- Cómo ejecutarlo:
--   1) Crear la base:   CREATE DATABASE "VisionCampus";
--   2) Conectarse a ella y ejecutar este archivo completo.
--   Se puede ejecutar varias veces sin errores (IF NOT EXISTS).
--
-- NOTA: los nombres "permanecia" y "porcetaje_ocupacion" tienen errores de
-- ortografía, pero el código del sistema ya los usa tal cual. No se corrigen
-- sin cambiar también el código.
-- ============================================================


-- ------------------------------------------------------------
-- 1. AULAS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.aulas (
    id        serial4     PRIMARY KEY,
    aula      varchar(50) NOT NULL,
    capacidad int4        NOT NULL
);


-- ------------------------------------------------------------
-- 2. EVENTOS (entradas y salidas)
--    tipo: 'ENTRADA' o 'SALIDA'
--    permanecia: segundos que la persona estuvo en el aula (solo en SALIDA)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.eventos (
    id         serial4     PRIMARY KEY,
    id_persona int4        NOT NULL,
    tipo       varchar(10) NOT NULL,
    hora       timestamp   NOT NULL,
    permanecia numeric     NULL,
    aula_id    int4        NOT NULL,
    CONSTRAINT eventos_aula_id_fkey
        FOREIGN KEY (aula_id) REFERENCES public.aulas (id)
);


-- ------------------------------------------------------------
-- 3. OCUPACION_HISTORICO (una fila cada pocos segundos)
--    estado: VACIA, DISPONIBLE, MEDIA, ALTA, LLENA o SATURACION
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.ocupacion_historico (
    id                  serial4     PRIMARY KEY,
    aula_id             int4        NOT NULL,
    hora                timestamp   NOT NULL,
    cantidad_personas   int4        NOT NULL,
    porcetaje_ocupacion numeric     NOT NULL,
    estado              varchar(20) NULL,
    CONSTRAINT ocupacion_historico_aula_id_fkey
        FOREIGN KEY (aula_id) REFERENCES public.aulas (id)
);


-- ------------------------------------------------------------
-- 4. ROSTROS_REGISTRADOS (solo voluntarios que autorizan su registro)
--    huella_facial: vector de 512 números (embedding), no es una foto
--    autorizado: false = persona registrada pero sin permiso (alerta roja)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.rostros_registrados (
    id_rostro      serial4      PRIMARY KEY,
    nombre         varchar(100) NOT NULL,
    huella_facial  float4[]     NOT NULL,
    fecha_registro timestamp    NOT NULL DEFAULT now(),
    autorizado     bool         NOT NULL
);


-- ------------------------------------------------------------
-- 5. ÍNDICES para consultas por aula y por hora (estadísticas)
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_eventos_aula_hora
    ON public.eventos (aula_id, hora);

CREATE INDEX IF NOT EXISTS idx_ocupacion_aula_hora
    ON public.ocupacion_historico (aula_id, hora);


-- ------------------------------------------------------------
-- 6. DATOS DE REFERENCIA: las aulas que usa el sistema
--    AULA-P6  -> aula real (la que mide la cámara)
--    AULA-SIM -> aula SIMULADA, solo para practicar y para el dashboard.
--                Sus datos nunca se mezclan con los reales
--                (los llena dashboard/generar_datos_simulados.py).
--    Cada aula se inserta solo si todavía no existe.
-- ------------------------------------------------------------
INSERT INTO public.aulas (aula, capacidad)
SELECT 'AULA-P6', 30
WHERE NOT EXISTS (SELECT 1 FROM public.aulas WHERE aula = 'AULA-P6');

INSERT INTO public.aulas (aula, capacidad)
SELECT 'AULA-SIM', 30
WHERE NOT EXISTS (SELECT 1 FROM public.aulas WHERE aula = 'AULA-SIM');
