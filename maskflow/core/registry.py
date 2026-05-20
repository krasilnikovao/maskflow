from maskflow.core.interfaces import BaseDetector, BaseMasker


class Registry:
    def __init__(self) -> None:
        self._detectors: dict[str, BaseDetector] = {}
        self._maskers: dict[str, BaseMasker] = {}

    def register_detector(self, detector: BaseDetector) -> None:
        if detector.name in self._detectors:
            raise ValueError(f"Detector already registered: {detector.name}")

        self._detectors[detector.name] = detector

    def register_masker(self, detector_name: str, masker: BaseMasker) -> None:
        if detector_name in self._maskers:
            raise ValueError(f"Masker already registered for detector: {detector_name}")

        self._maskers[detector_name] = masker

    @property
    def detectors(self) -> list[BaseDetector]:
        return list(self._detectors.values())

    @property
    def maskers(self) -> dict[str, BaseMasker]:
        return self._maskers.copy()
