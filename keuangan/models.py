from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_profile_picture_url(self):
        if self.profile_picture:
            return self.profile_picture.url
        return None


class Akun(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    nama = models.CharField(max_length=100)
    kode = models.CharField(max_length=10)
    tipe = models.CharField(max_length=20)  # Aktiva, Pasiva, Modal, dll

    class Meta:
        unique_together = ('user', 'kode')

    def __str__(self):
        return f"{self.kode} - {self.nama}"

class Transaksi(models.Model):
    tanggal = models.DateField()
    deskripsi = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.tanggal} - {self.deskripsi}"

class Jurnal(models.Model):
    transaksi = models.ForeignKey(Transaksi, on_delete=models.CASCADE)
    akun = models.ForeignKey(Akun, on_delete=models.CASCADE)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    kredit = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.transaksi} | {self.akun} | D: {self.debit} K: {self.kredit}"
