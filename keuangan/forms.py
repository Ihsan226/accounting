from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Transaksi, Akun, UserProfile

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com'
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nama Depan'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nama Belakang'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Konfirmasi Password'
        })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class TransaksiForm(forms.ModelForm):    
    akun_debet = forms.ModelChoiceField(
        queryset=Akun.objects.all(),
        empty_label="Pilih Akun Debet",
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    
    akun_kredit = forms.ModelChoiceField(
        queryset=Akun.objects.all(),
        empty_label="Pilih Akun Kredit",
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    
    jumlah = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': '0.00'
        })
    )

    class Meta:
        model = Transaksi
        fields = ['tanggal', 'deskripsi']
        widgets = {
            'tanggal': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'deskripsi': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Masukkan deskripsi transaksi...'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['akun_debet'].queryset = Akun.objects.filter(user=user).order_by('kode')
            self.fields['akun_kredit'].queryset = Akun.objects.filter(user=user).order_by('kode')
        else:
            self.fields['akun_debet'].queryset = Akun.objects.none()
            self.fields['akun_kredit'].queryset = Akun.objects.none()

class AkunForm(forms.ModelForm):
    TIPE_CHOICES = [
        ('Aktiva Lancar', 'Aktiva Lancar'),
        ('Aktiva Tetap', 'Aktiva Tetap'),
        ('Kewajiban Lancar', 'Kewajiban Lancar'),
        ('Kewajiban Jangka Panjang', 'Kewajiban Jangka Panjang'),
        ('Modal', 'Modal'),
        ('Pendapatan', 'Pendapatan'),
        ('Beban', 'Beban'),
    ]
    
    nama = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Masukkan nama akun'
        })
    )
    
    kode = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contoh: 1100, 2100, 3100'
        })
    )
    
    tipe = forms.ChoiceField(
        choices=TIPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    class Meta:
        model = Akun
        fields = ['kode', 'nama', 'tipe']


class UserProfileForm(forms.ModelForm):
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
            'id': 'profile-picture-input'
        })
    )
    
    bio = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Ceritakan sedikit tentang diri Anda...'
        })
    )

    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'bio']


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control'
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
