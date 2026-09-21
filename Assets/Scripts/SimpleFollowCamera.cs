using UnityEngine;

public class SimpleFollowCamera : MonoBehaviour
{
    public Transform target;
    public Vector3 offset = new Vector3(0f, 2.2f, -4.5f);
    public float followSpeed = 8f;
    public float lookHeightOffset = 1.5f;

    void LateUpdate()
    {
        if (target == null) return;
        Vector3 desiredPos = target.position + target.TransformDirection(offset);
        transform.position = Vector3.Lerp(transform.position, desiredPos, followSpeed * Time.deltaTime);
        transform.LookAt(target.position + Vector3.up * lookHeightOffset);
    }
}
