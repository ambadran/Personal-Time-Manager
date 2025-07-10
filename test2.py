
class Prayers(SessionGroup):
    PRAYERS_DAILY = [
            "FAJR",
            "DHUHR",
            "ASR",
            "MAGHRIB",
            "ISHA"]
    PRAYERS_WEEKLY = [
            "FAJR_SATURDAY",
            "DHUHR_SATURDAY",
            "ASR_SATURDAY",
            "MAGHRIB_SATURDAY",
            "ISHA_SATURDAY",
            "FAJR_SUNDAY",
            "DHUHR_SUNDAY",
            "ASR_SUNDAY",
            "MAGHRIB_SUNDAY",
            "ISHA_SUNDAY",
            "FAJR_MONDAY",
            "DHUHR_MONDAY",
            "ASR_MONDAY",
            "MAGHRIB_MONDAY",
            "ISHA_MONDAY",
            "FAJR_TUESDAY",
            "DHUHR_TUESDAY",
            "ASR_TUESDAY",
            "MAGHRIB_TUESDAY",
            "ISHA_TUESDAY",
            "FAJR_WEDNESDAY",
            "DHUHR_WEDNESDAY",
            "ASR_WEDNESDAY",
            "MAGHRIB_WEDNESDAY",
            "ISHA_WEDNESDAY",
            "FAJR_THURSDAY",
            "DHUHR_THURSDAY",
            "ASR_THURSDAY",
            "MAGHRIB_THURSDAY",
            "ISHA_THURSDAY",
            "FAJR_FRIDAY",
            "DHUHR_FRIDAY",
            "ASR_FRIDAY",
            "MAGHRIB_FRIDAY",
            "ISHA_FRIDAY"]
    def __init__(self, week_start_date: struct_time):
        #TODO: check if date is correct, a saturday day
        super().__init__(week_start_date)

    def get_prayer_time(self, prayer: str) -> struct_time:
        '''
        returns the struct_time of the time of a specific prayer within this week
        '''
        if prayer not in self.PRAYERS_WEEKLY:
            raise ValueError(f"Prayer name is wrong\nPlease choose from\n{self.PRAYERS_WEEKLY}")

    def csp_variables(self) -> list[Session]:
        pass

    def csp_domains(self) -> dict[Session: list[struct_time]]:
        pass


