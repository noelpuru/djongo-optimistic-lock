from django.db import models
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.contrib.admin.widgets import AdminIntegerFieldWidget


class ConcurrentUpdate(Exception):
    """
    Raised when a model can not be saved due to a concurrent update.
    """


class ReadonlyInput(forms.TextInput):
    """
    A HiddenInput would be perfect for version fields, but hidden
    inputs leave ugly empty rows in the admin. The version must
    be submitted, of course, to be checked, so we can't just use
    ModelAdmin.readonly_fields.

    Pending Django ticket #11277, this displays the version in an
    uneditable input so there's no empty row in the admin table.

    https://code.djangoproject.com/ticket/11277
    """
    def __init__(self, *args, **kwargs):
        super(ReadonlyInput, self).__init__(*args, **kwargs)
        # just readonly, because disabled won't submit the value
        self.attrs['readonly'] = 'readonly'


class VersionField(models.PositiveIntegerField):
    """
    An integer field to track versions. Every time the model is saved,
    it is incremented by one.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', 0)
        super(VersionField, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        widget = kwargs.get('widget')
        if widget:
            if issubclass(widget, AdminIntegerFieldWidget):
                widget = ReadonlyInput()
        else:
            widget = forms.HiddenInput
        kwargs['widget'] = widget
        return super(VersionField, self).formfield(**kwargs)


class VersionedMixin(object):
    """
    Model mixin implementing version checking during saving.
    When a concurrent update is detected, saving is aborted and
    ConcurrentUpdate will be raised.
    """

    def _do_update(self, base_qs, using, pk_val, values):
        version_field = self.get_version_field()

        # _do_update is called once for each model in the inheritance
        # hierarchy. We only care about the model with the version field.
        if version_field.model != base_qs.model:
            return super(VersionedMixin, self)._do_update(
                base_qs, using, pk_val, values)

        # pre_save may or may not have been called at this point, based on if
        # version_field is in update_fields. Since we need to reliably know the
        # old version, we can't increment there.
        old_version = version_field.value_from_object(self)
        setattr(self, version_field.attname, old_version + 1)

        # so increment it here instead. Now old_version is reliable.
        for i, value_tuple in enumerate(values):
            if isinstance(value_tuple[0], VersionField):
                assert old_version == value_tuple[2]
                values[i] = (
                    value_tuple[0],
                    value_tuple[1],
                    value_tuple[2] + 1,
                )

        filter_kwargs = {
            'pk': pk_val,
            version_field.attname: old_version,
        }

        nrows = base_qs.filter(**filter_kwargs)._update(values)
        if nrows < 1:
            raise ConcurrentUpdate
        else:
            return True

    def get_version_field(self):
        for field in self._meta.fields:
            if isinstance(field, VersionField):
                return field
        raise ImproperlyConfigured(
            'VersionedMixin models must have a VersionField')
