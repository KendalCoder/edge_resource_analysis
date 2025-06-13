class JobLoader:
    """
    JobLoader generates workloads based on the job below,
scienceRules:
- 'schedule(imagesampler-top): cronjob("imagesampler-top", "0 * * * *")'
- 'schedule(imagesampler-bottom): cronjob("imagesampler-bottom", "0 * * * *")'
- 'schedule(cloud-cover-top): cronjob("cloud-cover-top", "*/10 * * * *")'
- 'schedule(object-counter-bottom): cronjob("object-counter-bottom", "*/5 * * * *")'
- 'schedule(motion-detection-bottom): cronjob("motion-detection-bottom", "*/5 * * * *")'
- 'schedule(sound-event-detection): cronjob("sound-event-detection", "*/10 * * * *")'
    """
    def __init__(self):
        self.workloads = []
        self.index = 0
        self.load()

    def load(self):
        imagesampler = {
            "NAME": "imagesampler",
            "REQUEST_CPU": "100m",
            "REQUEST_MEMORY": "10Mi",
        }
        cloudcover = {
            "NAME": "cloudcover",
            "REQUEST_CPU": "1500m",
            "REQUEST_MEMORY": "2500Mi",
            "LABELS": {"resource.gpu": "true"},
        }
        objectcounter = {
            "NAME": "objectcounter",
            "REQUEST_CPU": "2000m",
            "REQUEST_MEMORY": "3Gi",
            "LABELS": {"resource.gpu": "true"},
        }
        motiondetection = {
            "NAME": "motiondetection",
            "REQUEST_CPU": "1000m",
            "REQUEST_MEMORY": "1Gi",
        }
        soundeventdetection = {
            "NAME": "soundeventdetection",
            "REQUEST_CPU": "1000m",
            "REQUEST_MEMORY": "200Mi",
        }
        self.workloads.extend([
            [imagesampler, cloudcover, objectcounter, motiondetection, soundeventdetection],
            [objectcounter, motiondetection],
            [cloudcover, objectcounter, motiondetection, soundeventdetection],
            [objectcounter, motiondetection],
            [cloudcover, objectcounter, motiondetection, soundeventdetection],
            [objectcounter, motiondetection],
            [cloudcover, objectcounter, motiondetection, soundeventdetection],
            [objectcounter, motiondetection],
            [cloudcover, objectcounter, motiondetection, soundeventdetection],
            [objectcounter, motiondetection],
        ])

    def __len__(self):
        return len(self.workloads)

    def __getitem__(self, index):
        return self.workloads[index]
    
    def next(self) -> list:
        next_workloads = self.workloads[self.index]
        self.index = (self.index+1) % len(self.workloads)
        return next_workloads