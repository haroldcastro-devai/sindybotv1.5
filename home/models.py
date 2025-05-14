from django.db import models
from django.utils import timezone


# Create your models here.
class TbRegAudio(models.Model):
    idtb_reg_audio = models.AutoField(primary_key=True)
    reg_n_gasera = models.CharField(max_length=45, blank=True, null=True)
    reg_contrato = models.IntegerField(blank=True, null=True)
    reg_fecha = models.DateField(blank=True, null=True)
    reg_tseguro1 = models.CharField(max_length=45, blank=True, null=True)
    reg_tseguro2 = models.CharField(max_length=45, blank=True, null=True)    
    reg_partaudioventa = models.CharField(max_length=45, blank=True, null=True)
    reg_tipoarchivo = models.CharField(max_length=45, blank=True, null=True)    
    reg_estado_venta = models.CharField(max_length=45, blank=True, null=True)
    reg_observ_audio = models.CharField(max_length=45, blank=True, null=True)
    reg_fechontrat = models.CharField(max_length=45, blank=True, null=True) 
    reg_pesoarch = models.CharField(max_length=45, blank=True, null=True) 
    class Meta:        
        db_table = 'tb_reg_audio'
        
        
class TbRegActividad(models.Model):
    idtb_actv = models.AutoField(primary_key=True)   
    reg_activ_fecha = models.DateField(blank=True, null=True)
    reg_activ_user = models.CharField(max_length=45, blank=True, null=True)
    reg_activ_archproc = models.CharField(max_length=45, blank=True, null=True)
    reg_sum_ventpos = models.CharField(max_length=45, blank=True, null=True)
    reg_sum_ventneg = models.CharField(max_length=45, blank=True, null=True)
    reg_tip_consulta = models.CharField(max_length=45, blank=True, null=True)
    reg_tip_dir = models.CharField(max_length=70, blank=True, null=True)
    class Meta:        
        db_table = 'tb_reg_activ'   


class LearningSbot(models.Model):
    id = models.AutoField(primary_key=True)
    transcripcion = models.TextField()
    resultado_auditoria = models.CharField(max_length=255)
    detalles_evaluacion = models.JSONField() 
    fecha_registro = models.DateTimeField()

    class Meta:
        db_table = 'learning_sbot'  
        
