"""FootAndBall (Komorowski et al., 2020; `dades/FONT-footandball.md`): el detector públic de pilota, amb els pesos
publicats, entrenats amb les càmeres 1 a 4 d'ISSIA-CNR.

- **Els pesos** es comproven per l'empremta i es llegeixen amb `weights_only=True`: un fitxer de PyTorch pot
  executar codi en carregar-se, i així només se'n llegeixen els tensors.
- **La imatge** s'omple per baix i per la dreta fins a un múltiple de 32 (la xarxa redueix la mida per 16 i en torna
  a pujar la meitat), i les pilotes que cauen a la vora omplerta no hi són.
- **La mida de la pilota:** amb la imatge a la meitat (la pilota de 5 px en lloc de 10) en troba poques o cap
  (`pilota/resultats/issia-footandball.md`). Amb `escala`, la imatge s'amplia (o s'encongeix) abans de passar-hi la
  xarxa, perquè la pilota hi faci la mida de l'entrenament, i les posicions tornen a la imatge de l'entrada.
- **El que en surt:** les `maxim` pilotes més probables de la imatge, amb el centre en píxels i la confiança (0-1).

PyTorch no és a les dependències de la cadena: s'hi afegeix només per córrer això, sense tocar el lock, amb
`uv run --with torch --with torchvision --with opencv-python-headless ...`.

**Sense LightGBM al mateix procés:** cadascun porta el seu OpenMP, i si LightGBM es carrega abans que PyTorch,
Python cau en crear el detector (sense cap missatge). Per això el detector s'atura abans si el troba carregat, i
les eines que el fan servir no importen la cadena sencera ni el banc.
"""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ARREL = Path(__file__).resolve().parents[2]
DIR_REPO = ARREL / "dades" / "footandball" / "repo"
PESOS = DIR_REPO / "models" / "model_20201019_1416_final.pth"
SHA_PESOS = "42fbc1f457fc34d804b403e26138524fc40facde303ccd7b4be73121e8da4cd5"
MULTIPLE = 32
MITJANA = np.array([0.485, 0.456, 0.406], np.float32)       # la normalització amb què es va entrenar
DESVIACIO = np.array([0.229, 0.224, 0.225], np.float32)


@dataclass(frozen=True)
class Candidats:
    x: np.ndarray               # (m,) píxels, de més a menys confiança
    y: np.ndarray
    confianca: np.ndarray


def omple(imatge: np.ndarray, multiple: int = MULTIPLE) -> np.ndarray:
    """La imatge amb zeros per baix i per la dreta fins que l'alçada i l'amplada són múltiples de `multiple`."""
    alt, ample = imatge.shape[:2]
    return np.pad(imatge, ((0, -alt % multiple), (0, -ample % multiple), (0, 0)))


def a_tensor(imatge_bgr: np.ndarray) -> np.ndarray:
    """BGR (alt, ample, 3) de 0 a 255 → (1, 3, alt, ample) normalitzat com a l'entrenament."""
    rgb = imatge_bgr[..., ::-1].astype(np.float32) / 255.0
    return ((rgb - MITJANA) / DESVIACIO).transpose(2, 0, 1)[None].copy()


def sha256(cami: Path) -> str:
    return hashlib.sha256(cami.read_bytes()).hexdigest()


def repo():
    """El codi de FootAndBall (`network`, `data`), importable. S'atura abans si LightGBM ja és carregat."""
    if "lightgbm" in sys.modules and "torch" not in sys.modules:
        raise RuntimeError("LightGBM ja és carregat: amb PyTorch després, al mateix procés, Python cau")
    if str(DIR_REPO) not in sys.path:
        sys.path.insert(0, str(DIR_REPO))


def xarxa(fase: str, maxim: int = 10, estat=None):
    """La xarxa fb1 amb els pesos publicats (comprovats per l'empremta), o amb `estat` si es dona."""
    repo()
    import torch
    from network import footandball

    if estat is None:
        if sha256(PESOS) != SHA_PESOS:
            raise ValueError(f"{PESOS}: l'empremta no és la de `dades/FONT-footandball.md`")
        estat = torch.load(PESOS, map_location="cpu", weights_only=True)
    model = footandball.model_factory("fb1", fase, ball_threshold=0.0, max_ball_detections=maxim)
    model.load_state_dict(estat)
    return model


class Detector:
    def __init__(self, maxim: int = 10, fils: int | None = None, estat=None) -> None:
        """`estat`: uns altres pesos; si no, els publicats."""
        repo()
        import torch
        from data.augmentation import BALL_LABEL

        if fils:
            torch.set_num_threads(fils)
        self._torch = torch
        self._etiqueta = BALL_LABEL
        self.model = xarxa("detect", maxim, estat)
        self.model.eval()

    def pilotes(self, imatge_bgr: np.ndarray, escala: float = 1.0) -> Candidats:
        """Les pilotes més probables, en píxels de `imatge_bgr`. `escala`: quant s'amplia la imatge per a la xarxa."""
        imatge = redimensiona(imatge_bgr, escala)
        alt, ample = imatge.shape[:2]
        with self._torch.no_grad():
            sortida = self.model(self._torch.from_numpy(a_tensor(omple(imatge))))[0]
        de_pilota = sortida["labels"].numpy() == self._etiqueta
        caixes = sortida["boxes"].numpy()[de_pilota]
        x, y = (caixes[:, 0] + caixes[:, 2]) / 2, (caixes[:, 1] + caixes[:, 3]) / 2
        dins = (x < ample) & (y < alt)
        ordre = np.argsort(-sortida["scores"].numpy()[de_pilota][dins], kind="stable")
        return Candidats(x=x[dins][ordre] / escala, y=y[dins][ordre] / escala,
                         confianca=sortida["scores"].numpy()[de_pilota][dins][ordre].astype(float))


def redimensiona(imatge: np.ndarray, escala: float) -> np.ndarray:
    """Per encongir es fa la mitjana de l'àrea (sense escales de serra); per ampliar, bilineal."""
    if escala == 1.0:
        return imatge
    import cv2

    return cv2.resize(imatge, None, fx=escala, fy=escala,
                      interpolation=cv2.INTER_AREA if escala < 1 else cv2.INTER_LINEAR)
